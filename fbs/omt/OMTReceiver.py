import cyomtlib as omt

import bpy
import logging
import numpy as np

from ..FrameBufferSharingClient import FrameBufferSharingClient

class OMTReceiver(FrameBufferSharingClient):
	def __init__(self, name: str = "OMTReceiver"):
		super().__init__(name)
		self.receiver = None
		self.video_frame = None

	def setup(self, servers):
		for source in servers:
			if source == self.name:
				self.receiver = omt.Receiver(source, video_format=omt.PreferredVideoFormat.BGRA)
				self.receiver.__enter__()

	def has_new_frame(self) -> bool:
		if not self.receiver:
			return False

		frame = self.receiver.receive(omt.FrameType.VIDEO, timeout_ms=0)
		if isinstance(frame, omt.VideoFrame):
			self.video_frame = frame
			return True
		return False

	def new_frame_image(self) -> bool:
		return self.has_new_frame()

	def apply_frame_to_image(self, target_image: bpy.types.Image):
		if not self.video_frame:
			return

		# packed() returns a (height, width, 4) uint8 BGRA view
		pixels = self.video_frame.packed()
		height, width = pixels.shape[0], pixels.shape[1]

		# Update image dimensions if needed
		if (target_image.generated_height != height or target_image.generated_width != width):
			target_image.scale(width, height)

		# Convert BGRA to RGBA and normalize
		rgba = pixels[:, :, [2, 1, 0, 3]]
		norm_texture = rgba.astype(np.float32) / 255.0

		target_image.pixels = norm_texture.flatten()

	def can_memory_buffer(self) -> bool:
		return False

	def create_memory_buffer(self, texture_name: str, size: int):
		logging.warning("OMT does not support memory buffer. Could not create memory buffer.")

	def read_memory_buffer(self, texture_name: str, buffer):
		logging.warning("OMT does not support memory buffer. Could not read memory buffer.")

	def release(self):
		if self.receiver:
			self.receiver.__exit__(None, None, None)
