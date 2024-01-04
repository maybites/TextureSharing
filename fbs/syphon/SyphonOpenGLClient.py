from argparse import Namespace, ArgumentParser
from typing import Optional, Any

import syphon

import logging

from ..FrameBufferSharingClient import FrameBufferSharingClient

class SyphonOpenGLClient(FrameBufferSharingClient):
	def __init__(self, name: str = "SyphonClient"):
		super().__init__(name)

		self.ctx: Optional[syphon.SyphonOpenGLClient] = None
		self.texture: Optional[Any] = None

	def setup(self, server):
		# setup metal syphon server
		self.ctx = syphon.SyphonOpenGLClient(server)

	def has_new_frame(self):
		return self.ctx.has_new_frame()

	def new_frame_image(self):
		return self.ctx.new_frame_image()

	def can_memory_buffer(self):
		return False

	def create_memory_buffer(self, texture_name: str, size: int):
		logging.warning("syphon does not support memory buffer. Could not create memory buffer.")

	def read_memory_buffer(self, texture_name: str, buffer):
		logging.warning("syphon does not support memory buffer. Could not read memory buffer.")

	def release(self):
		self.ctx.stop()
