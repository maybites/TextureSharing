from typing import Any
from cyndilib.receiver import Receiver
from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
from cyndilib.video_frame import VideoFrameSync

import bpy
import logging
import numpy as np

from ..FrameBufferSharingClient import FrameBufferSharingClient

class NDIReceiver(FrameBufferSharingClient):
	def __init__(self, name: str = "NDIReceiver"):
		super().__init__(name)
		self.receiver = None
		self.source = None
		self.video_frame = None

	def setup(self, servers):
		for source in servers:
			if source.name == self.name:
				# Create receiver with RGBX format and highest bandwidth
				self.receiver = Receiver(
					color_format=RecvColorFormat.RGBX_RGBA,
					bandwidth=RecvBandwidth.highest
				)
				
				# Create and set up video frame sync
				vf = VideoFrameSync()
				self.receiver.frame_sync.set_video_frame(vf)
				
				# Set source and connect
				self.receiver.set_source(source)
				self.source = source
				
				# Wait for connection
				while not self.receiver.is_connected():
					pass

	def has_new_frame(self) -> bool:
		if not self.receiver:
			return False
		
		# Use frame_sync to capture video
		self.receiver.frame_sync.capture_video()
		vf = self.receiver.frame_sync.video_frame
		if vf is not None and vf.get_data_size() > 0:
			self.video_frame = vf
			return True
		return False

	def new_frame_image(self) -> bool:
		return self.has_new_frame()
		
	def apply_frame_to_image(self, target_image: bpy.types.Image):
		if not self.video_frame:
			return

		# Get frame dimensions
		width, height = self.video_frame.get_resolution()
	
		# Update image dimensions if needed
		if (target_image.generated_height != height or target_image.generated_width != width):
			target_image.scale(width, height)

		# Convert frame data to numpy array and normalize
		# The VideoFrameSync object supports the buffer protocol directly
		norm_texture = (np.frombuffer(self.video_frame, dtype=np.uint8) / 255.0).astype(float)

		# Apply frame data
		target_image.pixels = norm_texture

	def can_memory_buffer(self) -> bool:
		return False

	def create_memory_buffer(self, texture_name: str, size: int):
		logging.warning("NDI does not support memory buffer. Could not create memory buffer.")

	def read_memory_buffer(self, texture_name: str, buffer):
		logging.warning("NDI does not support memory buffer. Could not read memory buffer.")

	def release(self):
		if self.receiver:
			self.receiver.__exit__(None, None, None)
