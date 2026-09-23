import logging
import threading
from fractions import Fraction

import numpy as np
from cyndilib.sender import Sender
from cyndilib.video_frame import VideoSendFrame
from cyndilib.wrapper.ndi_structs import FourCC

import bpy
import gpu
from gpu_extras.presets import draw_texture_2d

from ..FrameBufferSharingServer import FrameBufferSharingServer

class NDIServer(FrameBufferSharingServer):
    def __init__(self, name: str = "NDIServer", steady_stream: bool = False):
        super().__init__(name)
        self.sender: Sender | None = None
        self.video_frame: VideoSendFrame | None = None
        self.width: int = 1920
        self.height: int = 1080
        self.frame_rate: Fraction = Fraction(60)
        self.steady_stream = steady_stream
        self._latest_frame: tuple[np.ndarray, int, int] | None = None
        self._new_frame = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def setup(self):
        render = bpy.context.scene.render
        self.frame_rate = Fraction(render.fps) / Fraction(render.fps_base).limit_denominator(1001)

        # Create sender with the specified name
        self.sender = Sender(self.name)
        self._set_video_frame(self.width, self.height)

        # Start the sender
        self.sender.__enter__()

        self._stop.clear()
        self._thread = threading.Thread(target=self._send_loop, name=f"NDISender-{self.name}", daemon=True)
        self._thread.start()

    def _set_video_frame(self, width: int, height: int):
        self.video_frame = VideoSendFrame()
        self.video_frame.set_fourcc(FourCC.RGBA)
        self.video_frame.set_resolution(width, height)
        self.video_frame.set_frame_rate(self.frame_rate)
        self.sender.set_video_frame(self.video_frame)

    def _resize(self, width: int, height: int):
        # The video frame can only be replaced while the sender is closed
        self.sender.__exit__(None, None, None)
        self._set_video_frame(width, height)
        self.sender.__enter__()

    # Runs off the main thread because NDI clocks video sends, so each send blocks
    # for one frame period. With steady_stream the last frame is resent while the
    # viewport is idle. Only this thread touches the sender after setup().
    def _send_loop(self):
        current_size = (self.width, self.height)
        while not self._stop.is_set():
            if not self.steady_stream or self._latest_frame is None:
                if not self._new_frame.wait(0.1):
                    continue
            self._new_frame.clear()
            latest = self._latest_frame
            if latest is None or self._stop.is_set():
                continue
            data, width, height = latest
            try:
                if (width, height) != current_size:
                    self._resize(width, height)
                    current_size = (width, height)
                self.sender.write_video(data)
            except Exception:
                logging.exception("NDI send failed")
                self._stop.wait(0.1)

    def draw_texture(self, offscreen: gpu.types.GPUOffScreen, rect_pos: tuple[int, int], width: int, height: int):
        draw_texture_2d(offscreen.texture_color, rect_pos, width, height)

    def send_texture(self, offscreen: gpu.types.GPUOffScreen, width: int, height: int, is_flipped: bool = False):
        if not self.sender:
            return

        # Get texture from offscreen
        texture = offscreen.texture_color
        self.height = texture.height
        self.width = texture.width

        # Get texture data in 3d array
        texture_data = texture.read()

        # Blender 5.2 corrected GPU buffer strides (89a0750); transpose legacy layouts only.
        flat_np = np.asarray(texture_data, dtype=np.uint8)
        if flat_np.strides[-1] != flat_np.itemsize:
            flat_np = flat_np.transpose()

        # If texture is flipped, flip it vertically while preserving RGBA channels
        if is_flipped:
            # Reshape to (height, width, 4) to maintain RGBA channels
            flat_np = flat_np.reshape(self.height, self.width, 4)
            # Flip only the height dimension
            flat_np = np.flip(flat_np, axis=0)

        # Flatten the array from 3d to 1d. flatten() copies, so the send thread
        # can hold this array without it changing underneath.
        self._latest_frame = (flat_np.flatten(), self.width, self.height)
        self._new_frame.set()

    def can_memory_buffer(self):
        return False

    def create_memory_buffer(self, texture_name: str, size: int):
        logging.warning("ndi does not support memory buffer. Could not create memory buffer.")
        return

    def write_memory_buffer(self, texture_name: str, buffer):
        logging.warning("ndi does not support memory buffer. Could not write memory buffer.")
        return

    def release(self):
        self._stop.set()
        self._new_frame.set()
        if self._thread:
            self._thread.join()
            self._thread = None
        if self.sender:
            self.sender.__exit__(None, None, None)
            self.sender = None
