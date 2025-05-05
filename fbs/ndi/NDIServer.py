import logging
from typing import Optional

import numpy as np
from cyndilib.sender import Sender
from cyndilib.video_frame import VideoSendFrame
from cyndilib.wrapper.ndi_structs import FourCC

import gpu
from gpu_extras.presets import draw_texture_2d

from ..FrameBufferSharingServer import FrameBufferSharingServer

class NDIServer(FrameBufferSharingServer):
    def __init__(self, name: str = "NDIServer"):
        super().__init__(name)
        self.sender = None
        self.video_frame = None
        self.width = 1920
        self.height = 1080

    def setup(self):
        # Create sender with the specified name
        self.sender = Sender(self.name)
        
        # Create and configure video frame
        self.video_frame = VideoSendFrame()
        self.video_frame.set_fourcc(FourCC.RGBA)
        self.video_frame.set_resolution(self.width, self.height)
        
        # Add video frame to sender
        self.sender.set_video_frame(self.video_frame)
        
        # Pre-allocate bytearray and memoryview for frame data
        frame_size_bytes = self.video_frame.get_data_size()
        self.frame_buffer = bytearray(frame_size_bytes)
        self.frame_view = memoryview(self.frame_buffer)
        
        # Start the sender
        self.sender.__enter__()

    def draw_texture(self, offscreen: gpu.types.GPUOffScreen, rect_pos: tuple[int, int], width: int, height: int):
        draw_texture_2d(offscreen.texture_color, rect_pos, width, height)

    def send_texture(self, offscreen: gpu.types.GPUOffScreen, width: int, height: int, is_flipped: bool = False):
        if not self.sender:
            return

        # Get texture from offscreen
        texture = offscreen.texture_color
        
        # Update dimensions if changed
        if (texture.height != self.height or texture.width != self.width):
            self.height = texture.height
            self.width = texture.width
            
            # Close sender before updating video frame
            self.sender.__exit__(None, None, None)
            
            # Recreate video frame with new dimensions
            self.video_frame = VideoSendFrame()
            self.video_frame.set_fourcc(FourCC.RGBA)
            self.video_frame.set_resolution(self.width, self.height)
            self.sender.set_video_frame(self.video_frame)
            
            # Re-allocate buffer for new size
            frame_size_bytes = self.video_frame.get_data_size()
            self.frame_buffer = bytearray(frame_size_bytes)
            self.frame_view = memoryview(self.frame_buffer)
            
            # Reopen sender
            self.sender.__enter__()
        
        # Get texture data and ensure proper format
        texture_data = texture.read()

        lst = texture_data.to_list()

        # Convert to numpy array and ensure correct format
        flat_np = np.array(lst, dtype=np.uint8)

        # If texture is flipped, flip it vertically
        if is_flipped:
            flat_np = np.flipud(flat_np)
                    

        flat_tobytes = flat_np.tobytes()

        # Copy data into memoryview
        self.frame_view[:] = flat_tobytes
        
        # Send the frame
        self.sender.write_video_async(self.frame_view)

    def can_memory_buffer(self):
        return false

    def create_memory_buffer(self, texture_name: str, size: int):
        logging.warning("ndi does not support memory buffer. Could not create memory buffer.")
        return

    def write_memory_buffer(self, texture_name: str, buffer):
        logging.warning("syphon does not support memory buffer. Could not write memory buffer.")
        return

    def release(self):
        if self.sender:
            self.sender.__exit__(None, None, None)
