from abc import ABC, abstractmethod
import gpu
from sys import platform
from typing import Optional, Any

class FrameBufferDirectory(ABC):
	def __init__(self, name: str):
		self.name = name

	@abstractmethod
	def setup(self):
		pass

	@abstractmethod
	def update(self):
		pass

	@abstractmethod
	def has_servers(self):
		pass

	@staticmethod
	def create(name: str, server):
		if platform.startswith("darwin"):
			from .syphon.SyphonDirectory import SyphonDirectory
			return SyphonDirectory(name)
		elif platform.startswith("win"):
			from .spout.SpoutServer import SpoutServer
			return SpoutServer(name)
		else:
			raise Exception(f"Platform {platform} is not supported!")
