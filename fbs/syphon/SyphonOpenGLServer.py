from argparse import Namespace, ArgumentParser
from typing import Optional, Any

import numpy as np

from syphon import server as syphon_server

import gpu
from gpu_extras.presets import draw_texture_2d

import logging

from ..FrameBufferSharingServer import FrameBufferSharingServer

class SyphonOpenGLServer(FrameBufferSharingServer):
	def __init__(self, name: str = "SyphonServer"):
		super().__init__(name)

		self.ctx: Optional[syphon_server.SyphonOpenGLServer] = None

	def setup(self):
		# setup metal syphon server
		self.ctx = syphon_server.SyphonOpenGLServer(self.name)

	def draw_texture(self, offscreen: gpu.types.GPUOffScreen, rect_pos: tuple[int, int], width: int, height: int):
		draw_texture_2d(offscreen.color_texture, rect_pos, width, height)

	def send_texture(self, offscreen:  gpu.types.GPUOffScreen, width: int, height: int, is_flipped: bool = False):
		texture = offscreen.color_texture
		self.ctx.publish_frame_texture(texture, size=[width, height], is_flipped=is_flipped)

	def can_memory_buffer(self):
		return False

	def create_memory_buffer(self, texture_name: str, size: int):
		logging.warning("syphon does not support memory buffer. Could not create memory buffer.")

	def write_memory_buffer(self, texture_name: str, buffer):
		logging.warning("syphon does not support memory buffer. Could not write memory buffer.")

	def release(self):
		self.ctx.stop()
