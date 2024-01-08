from argparse import Namespace, ArgumentParser
from typing import Optional, Any

import syphon
from syphon.utils.raw import copy_mtl_texture_to_bytes
from syphon.utils.numpy import copy_mtl_texture_to_image

import logging
import bpy
import numpy as np

from ..FrameBufferSharingClient import FrameBufferSharingClient

class SyphonMetalClient(FrameBufferSharingClient):
	def __init__(self, name: str = "SyphonClient"):
		super().__init__(name)

		self.ctx: Optional[syphon.SyphonMetalClient] = None
		self.texture: Optional[Any] = None

	def setup(self, server):
		self.ctx = syphon.SyphonMetalClient(server)

	def has_new_frame(self):
		return self.ctx.has_new_frame

	def new_frame_image(self):
		return self.ctx.new_frame_image

	def apply_frame_to_image(self, target_image: bpy.types.Image):
		new_texture = self.new_frame_image()
		height = new_texture.height()
		width = new_texture.width()
	
		if (target_image.generated_height != height or target_image.generated_width != width):
			target_image.scale(width, height)

		image = copy_mtl_texture_to_image(new_texture)
		byte_to_normalized = 1.0 / 255.0
		target_image.pixels[:] = (image.astype(float) * byte_to_normalized).ravel()

	def can_memory_buffer(self):
		return False

	def create_memory_buffer(self, texture_name: str, size: int):
		logging.warning("syphon does not support memory buffer. Could not create memory buffer.")

	def read_memory_buffer(self, texture_name: str, buffer):
		logging.warning("syphon does not support memory buffer. Could not read memory buffer.")

	def release(self):
		self.ctx.stop()
