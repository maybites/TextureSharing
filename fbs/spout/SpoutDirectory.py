from argparse import Namespace, ArgumentParser
from typing import Optional, Any, List

import SpoutGL

from ..FrameBufferDirectory import FrameBufferDirectory


class SpoutDirectory(FrameBufferDirectory):
    def __init__(self, name: str = "SpoutDirectory"):
        super().__init__(name)
        self.sources: Optional[List[str]] = []  # sources or servers

    def setup(self):
        self.receiver = SpoutGL.SpoutReceiver()
        self.update()

    def update(self):
        self._reset()
        # Add getSenderList(), getSenderInfo(), getActiveSender(), setActiveSender()
        # available from 0.1.0 of SpoutGL

        sender_names = self.receiver.getSenderList()
        sender_list = [self.receiver.getSenderInfo(n) for n in sender_names]
        # to access sender_info.width, sender_info.height

        print(sender_names, sender_list)
        self.sources = sender_names
        print("spout sources", self.sources)

        for i, s in enumerate(self.sources):
            self.directory.add((s, s, s, "WORLD_DATA", i))

        self.register()

    def has_servers(self):
        return not not self.sources

    def get_servers(self):
        return self.sources
