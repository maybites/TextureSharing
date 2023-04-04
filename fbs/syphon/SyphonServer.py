from argparse import Namespace, ArgumentParser
from typing import Optional, Any

import numpy as np
import syphonpy

import logging

from ..FrameBufferSharingServer import FrameBufferSharingServer


class SyphonServer(FrameBufferSharingServer):
	def __init__(self, name: str = "SyphonServer"):
		super().__init__(name)

		self.ctx: Optional[syphonpy.SyphonServer] = None

	def setup(self):
		# setup spout
		self.ctx = syphonpy.SyphonServer(self.name)
		if self.ctx.error_state():
			logging.error("error in Syphonserver")

	def send_texture(self, texture_id: int, width: int, height: int, is_flipped: bool = False):
		self.ctx.publish_frame_texture(texture_id,
									   syphonpy.MakeRect(0, 0, width, height),
									   syphonpy.MakeSize(width, height), is_flipped)

	def can_memory_buffer(self):
		return False

	def create_memory_buffer(self, texture_name: str, size: int):
		logging.warning("syphon does not support memory buffer. Could not create memory buffer.")

	def write_memory_buffer(self, texture_name: str, buffer):
		logging.warning("syphon does not support memory buffer. Could not write memory buffer.")

	def release(self):
		self.ctx.stop()
