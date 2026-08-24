import logging
from argparse import ArgumentParser, Namespace
from typing import Optional

import numpy as np
import SpoutGL

import gpu
from gpu_extras.presets import draw_texture_2d

from ..FrameBufferSharingServer import FrameBufferSharingServer

# OpenGL constants
GL_RGBA = 0x1908
GL_BGRA = 0x80E1


class SpoutServer(FrameBufferSharingServer):
    def __init__(self, name: str = "SpoutServer"):
        super().__init__(name)
        self.ctx: Optional[SpoutGL.SpoutSender] = None
        self.width: int = 1920
        self.height: int = 1080

    def setup(self):
        # setup spout
        self.ctx = SpoutGL.SpoutSender()
        self.ctx.setSenderName(self.name)

    def draw_texture(self, offscreen: gpu.types.GPUOffScreen, rect_pos: tuple[int, int], width: int, height: int):
        draw_texture_2d(offscreen.texture_color, rect_pos, width, height)

    def send_texture(self, offscreen: gpu.types.GPUOffScreen, width: int, height: int, is_flipped: bool = False):
        if not self.ctx:
            return
        
        # Get texture from offscreen
        texture = offscreen.texture_color
        
        # Update dimensions
        self.height = texture.height
        self.width = texture.width
        
        # Read texture data
        texture_data = texture.read()
        
        # Blender 5.2 corrected GPU buffer strides (89a0750); transpose legacy layouts only.
        flat_np = np.asarray(texture_data, dtype=np.uint8)
        if flat_np.strides[-1] != flat_np.itemsize:
            flat_np = flat_np.transpose()
        
        # Reshape to image array (height, width, 4)
        image_array = flat_np.reshape(self.height, self.width, 4)
        
        # Flip vertically if needed
        if is_flipped:
            image_array = np.flip(image_array, axis=0)
        
        # Flatten and make contiguous
        pixels = np.ascontiguousarray(image_array.flatten())
        
        # Send image via SpoutGL
        success = self.ctx.sendImage(pixels, self.width, self.height, GL_RGBA, False, 0)
        
        if not success:
            logging.warning("Could not send spout image.")
            return
        
        # Indicate that a frame is ready to read
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
        if self.ctx:
            self.ctx.releaseSender()