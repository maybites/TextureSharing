import logging
import threading

import numpy as np
import cyomtlib as omt

import bpy
import gpu
from gpu_extras.presets import draw_texture_2d

from ..FrameBufferSharingServer import FrameBufferSharingServer

class OMTServer(FrameBufferSharingServer):
	def __init__(self, name: str = "OMTServer", steady_stream: bool = False):
		super().__init__(name)
		self.sender: omt.Sender | None = None
		self.width: int = 1920
		self.height: int = 1080
		self.frame_rate: float = 60
		self.steady_stream = steady_stream
		self._latest_frame: np.ndarray | None = None
		self._new_frame = threading.Event()
		self._stop = threading.Event()
		self._thread: threading.Thread | None = None

	def setup(self):
		render = bpy.context.scene.render
		self.frame_rate = render.fps / render.fps_base

		self.sender = omt.Sender(self.name)
		self.sender.__enter__()

		self._stop.clear()
		self._thread = threading.Thread(target=self._send_loop, name=f"OMTSender-{self.name}", daemon=True)
		self._thread.start()

	# Runs off the main thread because send_video blocks for one frame period.
	# With steady_stream the last frame is resent while the viewport is idle.
	def _send_loop(self):
		while not self._stop.is_set():
			if not self.steady_stream or self._latest_frame is None:
				if not self._new_frame.wait(0.1):
					continue
			self._new_frame.clear()
			frame = self._latest_frame
			if frame is None or self._stop.is_set():
				continue
			try:
				self.sender.send_video(frame, omt.Codec.BGRA, frame_rate=self.frame_rate, flags=omt.VideoFlags.ALPHA)
			except Exception:
				logging.exception("OMT send failed")
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

		# Reshape to (height, width, 4) RGBA
		frame = flat_np.reshape(self.height, self.width, 4)

		# If texture is flipped, flip it vertically while preserving RGBA channels
		if is_flipped:
			frame = np.flip(frame, axis=0)

		# Convert RGBA to BGRA, which is what send_video expects for packed formats.
		# This is a fresh array each call, so the send thread can hold it without a copy.
		self._latest_frame = np.ascontiguousarray(frame[..., [2, 1, 0, 3]])
		self._new_frame.set()

	def can_memory_buffer(self):
		return False

	def create_memory_buffer(self, texture_name: str, size: int):
		logging.warning("omt does not support memory buffer. Could not create memory buffer.")
		return

	def write_memory_buffer(self, texture_name: str, buffer):
		logging.warning("omt does not support memory buffer. Could not write memory buffer.")
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
