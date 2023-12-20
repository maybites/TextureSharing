from abc import ABC, abstractmethod
import gpu
from sys import platform
from typing import Optional, Any

import numpy as np

class FrameBufferSharingServer(ABC):
	def __init__(self, name: str):
		self.name = name

	@abstractmethod
	def draw_texture(self, offscreen: gpu.types.GPUOffScreen, rect_pos: tuple[int, int], width: int, height: int):
		pass

	@abstractmethod
	def send_texture(self, offscreen:  gpu.types.GPUOffScreen, width: int, height: int, is_flipped: bool = False):
		pass

	@abstractmethod
	def can_memory_buffer(self):
		pass

	@abstractmethod
	def create_memory_buffer(self, texture_name: str, size: int):
		pass

	@abstractmethod
	def write_memory_buffer(self, texture_name: str, buffer):
		pass

	@staticmethod
	def create(name: str):
		if platform.startswith("darwin"):
			if gpu.platform.backend_type_get() == 'METAL':
				from .syphon.SyphonMetalServer import SyphonMetalServer
				return SyphonMetalServer(name)
			if gpu.platform.backend_type_get() == 'OPENGL':
				from .syphon.SyphonOpenGLServer import SyphonOpenGLServer
				return SyphonOpenGLServer(name)
		elif platform.startswith("win"):
			from .spout.SpoutServer import SpoutServer
			return SpoutServer(name)
		else:
			raise Exception(f"Platform {platform} is not supported!")
