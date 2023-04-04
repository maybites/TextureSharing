import logging
from argparse import ArgumentParser, Namespace
from typing import Optional

import SpoutGL
import numpy as np
import bgl

from ..FrameBufferSharingServer import FrameBufferSharingServer


class SpoutServer(FrameBufferSharingServer):
    def __init__(self, name: str = "SpoutServer"):
        super().__init__(name)
        self.ctx: Optional[SpoutGL.SpoutSender] = None

    def setup(self):
        # setup spout
        self.ctx = SpoutGL.SpoutSender()
        self.ctx.setSenderName(self.name)

    def send_texture(self, texture_id: int, width: int, height: int, is_flipped: bool = False):
        success = self.ctx.sendTexture(
            texture_id, bgl.GL_TEXTURE_2D, width, height, is_flipped, 0)

        if not success:
            logging.warning("Could not send spout texture.")
            return

        self.ctx.setFrameSync(self.name)

    def can_memory_buffer(self):
        return True

    def create_memory_buffer(self, texture_name: str, size: int):
        success = self.ctx.createMemoryBuffer(texture_name, size)

        if not success:
            logging.warning("Could not create memory buffer.")

        return

    def write_memory_buffer(self, texture_name: str, buffer):
        success = self.ctx.writeMemoryBuffer(texture_name, buffer, len(buffer))

        if not success:
            logging.warning("Could not write memory buffer.")

        return

    def release(self):
        self.ctx.releaseSender()
