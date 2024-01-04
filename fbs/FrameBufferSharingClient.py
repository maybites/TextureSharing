from abc import ABC, abstractmethod
import gpu
from sys import platform
from typing import Optional, Any

class FrameBufferSharingClient(ABC):
	def __init__(self, name: str):
		self.name = name

	@abstractmethod
	def setup(self, server):
		pass

	@abstractmethod
	def has_new_frame(self):
		pass

	@abstractmethod
	def new_frame_image(self):
		pass

	@abstractmethod
	def can_memory_buffer(self):
		pass

	@abstractmethod
	def create_memory_buffer(self, texture_name: str, size: int):
		pass

	@abstractmethod
	def read_memory_buffer(self, texture_name: str, buffer):
		pass

	@staticmethod
	def create(name: str, server):
		if platform.startswith("darwin"):
			if gpu.platform.backend_type_get() == 'METAL':
				from .syphon.SyphonMetalClient import SyphonMetalClient
				return SyphonMetalClient(name, server)
			if gpu.platform.backend_type_get() == 'OPENGL':
				from .syphon.SyphonOpenGLClient import SyphonOpenGLClient
				return SyphonOpenGLClient(name, server)
		elif platform.startswith("win"):
			from .spout.SpoutServer import SpoutServer
			return SpoutServer(name)
		else:
			raise Exception(f"Platform {platform} is not supported!")
