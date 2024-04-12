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
		ndi.find_wait_for_sources(self.ndi_find, 5000)
		self.sources = ndi.find_get_current_sources(self.ndi_find)

		for i, s in enumerate(self.sources):
			self.directory.add((s.ndi_name, s.ndi_name, s.ndi_name, "WORLD_DATA", i))

		self.register()

	def has_servers(self):
		return not not self.sources

	def get_servers(self):
		return self.sources
	
	def unregister(self):
		ndi.find_destroy(self.ndi_find)
		super().unregister(self)


