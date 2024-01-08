from abc import ABC, abstractmethod
import bpy
from sys import platform
from typing import Optional, Any

class FrameBufferDirectory(ABC):
	def __init__(self, name: str):
		self.name = name
		self.directory = {}
		self._reset()
	
	def _reset(self):
		self.directory = {
    		("OFF", "Off", "No server selected", "WORLD_DATA", -1)
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
	def get_server(self, server_name):
		pass

	def register(self):
		bpy.types.Scene.TEXS_servers = bpy.props.EnumProperty(
        	items=self.directory,
        	name="Server",
			default="OFF"
		)

	def unregister(self):
		del bpy.types.Scene.TEXS_servers

	@staticmethod
	def create(name: str):
		if platform.startswith("darwin"):
			from .syphon.SyphonDirectory import SyphonDirectory
			return SyphonDirectory(name)
		elif platform.startswith("win"):
			from .spout.SpoutDirectory import SpoutDirectory
			return SpoutDirectory(name)
		else:
			raise Exception(f"Platform {platform} is not supported!")
