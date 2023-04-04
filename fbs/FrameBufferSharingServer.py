from abc import ABC, abstractmethod
from sys import platform
from typing import Optional, Any

import numpy as np

class FrameBufferSharingServer(ABC):
	def __init__(self, name: str):
		self.name = name

	@abstractmethod
	def send_texture(self, texture_id: int, width: int, height: int, is_flipped: bool = False):
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
			from .syphon.SyphonServer import SyphonServer
			return SyphonServer(name)
		elif platform.startswith("win"):
			from .spout.SpoutServer import SpoutServer
			return SpoutServer(name)
		else:
			raise Exception(f"Platform {platform} is not supported!")
