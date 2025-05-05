from typing import Optional, Any
from cyndilib.finder import Finder
from cyndilib.wrapper.ndi_structs import FourCC

import logging

from ..FrameBufferDirectory import FrameBufferDirectory

class NDIDirectory(FrameBufferDirectory):
	def __init__(self, name: str = "NDInDirectory"):
		super().__init__(name)
		self.finder = None
		self.sources = None

	def setup(self):
		self.finder = Finder()
		self.update()

	def update(self):
		self._reset()
		# Wait for sources with a timeout of 5 seconds
		self.finder.wait_for_sources(5)
		
		# Get current sources
		self.sources = list(self.finder)
		
		for i, source in enumerate(self.sources):
			self.directory.add((source.name, source.name, source.name, "WORLD_DATA", i))

		self.register()

	def has_servers(self) -> bool:
		return bool(self.sources)

	def get_servers(self) -> list:
		return self.sources if self.sources else []
	
	def unregister(self):
		if self.finder:
			self.finder.__exit__(None, None, None)
		super().unregister()


