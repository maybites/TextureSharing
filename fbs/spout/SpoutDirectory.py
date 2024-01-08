from argparse import Namespace, ArgumentParser
from typing import Optional, Any

import SpoutGL

import logging

from ..FrameBufferDirectory import FrameBufferDirectory

class SpoutDirectory(FrameBufferDirectory):
	def __init__(self, name: str = "SpoutDirectory"):
		super().__init__(name)

		# self.ctx: Optional[SpoutGL.SpoutClient] = None		
		# self.servers: Optional[syphon.SyphonServerDescription] = None

	def setup(self):
		self.update()

	def update(self):
		self._reset()
		self.register()

	def has_servers(self):
		return False

	def get_server(self, server_name):
		return None
