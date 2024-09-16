from abc import ABC, abstractmethod
import bpy
import gpu
from sys import platform
from typing import Optional, Any

class FrameBufferSharingClient(ABC):
	def __init__(self, name: str):
		self.name = name

	@abstractmethod
	def setup(self, servers):
		pass

	@abstractmethod
	def has_new_frame(self):
		pass

	@abstractmethod
	def new_frame_image(self):
		pass

	@abstractmethod
	def apply_frame_to_image(self, target_image: bpy.types.Image):
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
	def create(name: str, type: str):
		if type == "SPOUT":
			if platform.startswith("darwin"):
				if gpu.platform.backend_type_get() == 'METAL':
					from .syphon.SyphonMetalClient import SyphonMetalClient
					return SyphonMetalClient(name)
				if gpu.platform.backend_type_get() == 'OPENGL':
					from .syphon.SyphonOpenGLClient import SyphonOpenGLClient
					return SyphonOpenGLClient(name)
			elif platform.startswith("win"):
				from .spout.SpoutClient import SpoutClient
				return SpoutClient(name)
			else:
				raise Exception(f"Platform {platform} is not supported!")
		else:
			from .ndi.NDIReceiver import NDIReceiver
			return NDIReceiver(name)

	def timer_call(self, guivars):
		if self.has_new_frame() == True:
			self.apply_frame_to_image(guivars.texs_image)
			guivars.texs_image.update()
			guivars.texs_image.update_tag()
		
		return guivars.refresh_rate / 1000 if guivars.enable == 1 else None
