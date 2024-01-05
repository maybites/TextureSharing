from abc import ABC, abstractmethod
import gpu
from sys import platform
from typing import Optional, Any

class FrameBufferDirectory(ABC):
	def __init__(self, name: str):
		self.name = name
		self.directory = {}
		self._reset()
	
	def _reset(self):
		self.directory = {
    		("OFF", "Off", "No server selected", "IMPORT", -1)
    	}

	@abstractmethod
	def setup(self):
		pass

	@abstractmethod
	def update(self):
		pass

	@abstractmethod
	def has_servers(self):
		pass

	@abstractmethod
	def get_server(self, index):
		pass

	@staticmethod
	def create(name: str):
		if platform.startswith("darwin"):
			from .syphon.SyphonDirectory import SyphonDirectory
			return SyphonDirectory(name)
		elif platform.startswith("win"):
			from .spout.SpoutServer import SpoutServer
			return SpoutServer(name)
		else:
			raise Exception(f"Platform {platform} is not supported!")
