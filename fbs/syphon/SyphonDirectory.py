from argparse import Namespace, ArgumentParser
from typing import Optional, Any

import syphon

import logging

from ..FrameBufferDirectory import FrameBufferDirectory

class SyphonDirectory(FrameBufferDirectory):
	def __init__(self, name: str = "SyphonDirectory"):
		super().__init__(name)

		self.ctx: Optional[syphon.SyphonServerDirectory] = None
		self.servers: Optional[syphon.SyphonServerDescription] = None

	def setup(self):
		self.ctx = syphon.SyphonServerDirectory()
		self.update()

	def update(self):
		self._reset()
		self.ctx.update_run_loop()
		self.servers = self.ctx.servers
		index = 0
		for server in self.servers:
			self.directory.add((server.app_name, server.app_name, server.name, "IMPORT", index))
			index += 1

	def has_servers(self):
		return not not self.servers

	def get_server(self, index):
		return self.servers[index]
