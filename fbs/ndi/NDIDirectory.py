from argparse import Namespace, ArgumentParser
from typing import Optional, Any

import NDIlib as ndi

import logging

from ..FrameBufferDirectory import FrameBufferDirectory

class NDIDirectory(FrameBufferDirectory):
	def __init__(self, name: str = "NDInDirectory"):
		super().__init__(name)

		self.ndi_find = None
		self.sources = None

	def setup(self):
		self.ndi_find = ndi.find_create_v2()
		self.update()

	def update(self):
		self._reset()
		self.sources = ndi.find_get_current_sources(self.ndi_find)

		for i, s in enumerate(self.sources):
			self.directory.add((s.ndi_name, s.ndi_name, s.ndi_name, "WORLD_DATA", i))

            #print('%s. %s' % (i + 1, s.ndi_name))
		self.register()

	def has_servers(self):
		return not not self.sources

	def get_server(self, server_name):
		for items in self.directory:
			if items[0] == server_name:
				return self.sources[items[4]]
