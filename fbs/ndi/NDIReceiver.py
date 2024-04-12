from argparse import Namespace, ArgumentParser
from typing import Optional, Any

import NDIlib as ndi

import bpy
import logging
import numpy as np

from ..FrameBufferSharingClient import FrameBufferSharingClient

class NDIReceiver(FrameBufferSharingClient):
	def __init__(self, name: str = "NDIReceiver"):
		super().__init__(name)

		self.ndi_receive_create = None        
		self.ndi_receive = None
		self.video_frame = None
		self.ndi_find = None
		self.source = None

	def setup(self, sources):
		for source in sources:
			if source.ndi_name == self.name:
				self.ndi_receive_create = ndi.RecvCreateV3()
				self.ndi_receive_create.color_format = ndi.RECV_COLOR_FORMAT_RGBX_RGBA
				self.ndi_receive = ndi.recv_create_v3(self.ndi_receive_create)

				ndi.recv_connect(self.ndi_receive, source)

	def has_new_frame(self):
		t, self.video_frame, a, _ = ndi.recv_capture_v2(self.ndi_receive, 50)
		if t == ndi.FRAME_TYPE_VIDEO:
			return True

	def new_frame_image(self):
		t, self.video_frame, a, _ = ndi.recv_capture_v2(self.ndi_receive, 50)
		if t == ndi.FRAME_TYPE_VIDEO:
			return True
		
	def apply_frame_to_image(self, target_image: bpy.types.Image):
		#new_texture = np.copy(self.video_frame.data)
		#flat_texture = new_texture.flatten()
		#norm_texture = (flat_texture / 255.0).astype(float)

		norm_texture = (self.video_frame.data.flatten() / 255.0).astype(float)

		width = self.video_frame.xres
		height = self.video_frame.yres
	
		if (target_image.generated_height != height or target_image.generated_width != width):
			target_image.scale(width, height)

		target_image.pixels = norm_texture
		ndi.recv_free_video_v2(self.ndi_receive, self.video_frame)

	def can_memory_buffer(self):
		return False

	def create_memory_buffer(self, texture_name: str, size: int):
		logging.warning("NDI does not support memory buffer. Could not create memory buffer.")

	def read_memory_buffer(self, texture_name: str, buffer):
		logging.warning("NDI does not support memory buffer. Could not read memory buffer.")

	def release(self):
		ndi.recv_destroy(self.ndi_receive)
