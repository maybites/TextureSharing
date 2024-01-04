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
		self.servers = self.ctx.servers
		for server in self.servers:
			print(f"{server.app_name} ({server.uuid})")

	def update(self):
		self.ctx.update_run_loop()
		self.servers = self.ctx.servers
	
	def has_servers(self):
		return not not self.servers

