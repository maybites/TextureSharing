import cyomtlib as omt

from ..FrameBufferDirectory import FrameBufferDirectory

class OMTDirectory(FrameBufferDirectory):
	def __init__(self, name: str = "OMTDirectory"):
		super().__init__(name)
		self.sources = None

	def setup(self):
		self.update()

	def update(self):
		self._reset()
		# Wait for sources with a timeout of 5 seconds
		self.sources = omt.discover(wait=5.0)

		for i, source in enumerate(self.sources):
			self.directory.add((source, source, source, "WORLD_DATA", i))

		self.register()

	def has_servers(self) -> bool:
		return bool(self.sources)

	def get_servers(self) -> list:
		return self.sources if self.sources else []
