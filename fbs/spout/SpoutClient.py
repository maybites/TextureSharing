from argparse import Namespace, ArgumentParser
from typing import Optional, Any

import SpoutGL

import logging
import bpy

from ..FrameBufferSharingClient import FrameBufferSharingClient

class SpoutClient(FrameBufferSharingClient):
	def __init__(self, name: str = "SyphonClient"):
		super().__init__(name)

		self.ctx: Optional[SpoutGL.SpoutClient] = None
		self.texture: Optional[Any] = None

	def setup(self, server):
		# self.ctx = SpoutGL.SpoutClient(server)
		pass

	def has_new_frame(self):
		pass

	def new_frame_image(self):
		pass

	def apply_frame_to_image(self, target_image: bpy.types.Image):
		pass

	def can_memory_buffer(self):
		return True

	def create_memory_buffer(self, texture_name: str, size: int):
		success = self.ctx.createMemoryBuffer(texture_name, size)

		if not success:
			logging.warning("Could not create memory buffer.")

		return
	
	def read_memory_buffer(self, texture_name: str, buffer):
		success = self.ctx.readMemoryBuffer(texture_name, buffer, len(buffer))

		if not success:
			logging.warning("Could not write memory buffer.")
		
		return
	
	def release(self):
		self.ctx.stop()
