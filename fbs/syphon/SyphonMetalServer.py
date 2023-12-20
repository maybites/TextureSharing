from argparse import Namespace, ArgumentParser
from typing import Optional, Any

import numpy as np

from syphon import server as syphon_server
from syphon.utils.raw import copy_bytes_to_mtl_texture
from syphon.utils.raw import create_mtl_texture

import gpu
from gpu_extras.presets import draw_texture_2d

import logging

from ..FrameBufferSharingServer import FrameBufferSharingServer

class SyphonMetalServer(FrameBufferSharingServer):
	def __init__(self, name: str = "SyphonServer"):
		super().__init__(name)

		self.ctx: Optional[syphon_server.SyphonMetalServer] = None
		self.texture: Optional[Any] = None

	def setup(self):
		# setup metal syphon server
		self.ctx = syphon_server.SyphonMetalServer(self.name)

	def draw_texture(self, offscreen: gpu.types.GPUOffScreen, rect_pos: tuple[int, int], width: int, height: int):
		draw_texture_2d(offscreen.texture_color, rect_pos, width, height)

	def send_texture(self, offscreen:  gpu.types.GPUOffScreen, width: int, height: int, is_flipped: bool = False):
		texture = offscreen.texture_color
		if self.texture is None:
		    # create metal texture
			self.texture = create_mtl_texture(self.ctx.device, width, height)

		buffer = texture.read()
		copy_bytes_to_mtl_texture(buffer, self.texture)
		self.ctx.publish_frame_texture(self.texture, size=[width, height], is_flipped=is_flipped)

	def can_memory_buffer(self):
		return False

	def create_memory_buffer(self, texture_name: str, size: int):
		logging.warning("syphon does not support memory buffer. Could not create memory buffer.")

	def write_memory_buffer(self, texture_name: str, buffer):
		logging.warning("syphon does not support memory buffer. Could not write memory buffer.")

	def release(self):
		self.ctx.stop()
