from argparse import Namespace, ArgumentParser
from typing import Optional, Any, List

import SpoutGL

import logging

from ..FrameBufferDirectory import FrameBufferDirectory

class SpoutDirectory(FrameBufferDirectory):
	def __init__(self, name: str = "SpoutDirectory"):
		super().__init__(name)

		self.senderCnt: Optional[int] = 0
		self.servers:  Optional[List[str]] = []

	def setup(self):
		#self.senderCnt = Spout.GetSenderCount()

		self.update()

	def update(self):
		self._reset()
		#self.ctx.GetSenderNames(self.servers)
		index = 0
		for server in self.servers:
			server_title = server
			print(server)
			#if server.name != '':
			#	server_title = server_title + " | " + server.name

			#self.directory.add((server_title, server_title, server_title, "WORLD_DATA", index))
			#index += 1

		self.register()

	def has_servers(self):
		return False

	def get_servers(self, server_name):
		return None
