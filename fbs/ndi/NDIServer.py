import logging
from argparse import ArgumentParser, Namespace
from typing import Optional

import numpy as np

import NDIlib as ndi

import gpu

from ..FrameBufferSharingServer import FrameBufferSharingServer

class NDIServer(FrameBufferSharingServer):
    def __init__(self, name: str = "NDIServer"):
        super().__init__(name)
        self.send_settings = None
        self.ndi_send = None
        self.video_frame = None

        self.width = 1920
        self.height = 1080

    def setup(self):
        # setup spout

        self.send_settings  = ndi.SendCreate()
        self.send_settings.ndi_name = self.name

        self.ndi_send = ndi.send_create(self.send_settings)

        self.video_frame = ndi.VideoFrameV2()
        self.video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_BGRX
        self.video_frame.frame_format_type  = ndi.FRAME_FORMAT_TYPE_PROGRESSIVE

    def draw_texture(self, offscreen: gpu.types.GPUOffScreen, rect_pos: tuple[int, int], width: int, height: int):
        draw_texture_2d(offscreen.color_texture, rect_pos, width, height)

    def send_texture(self, offscreen:  gpu.types.GPUOffScreen, width: int, height: int, is_flipped: bool = False):
        # offscreen is type https://docs.blender.org/api/current/gpu.types.html#gpu.types.GPUOffScreen
        texture = offscreen.texture_color # returns https://docs.blender.org/api/current/gpu.types.html#gpu.types.GPUTexture
        
        if (texture.height != self.height or texture.width != self.width):
            self.height = texture.height
            self.width = texture.width
            self.video_frame.xres = self.width
            self.video_frame.yres = self.height

        self.video_frame.data = texture.read()        
        self.video_frame.line_stride_in_bytes  = self.width * 4
        
        ndi.send_send_video_v2(self.ndi_send, self.video_frame)

    def can_memory_buffer(self):
        return True

    def create_memory_buffer(self, texture_name: str, size: int):
        logging.warning("ndi does not support memory buffer. Could not create memory buffer.")
        return

    def write_memory_buffer(self, texture_name: str, buffer):
        logging.warning("syphon does not support memory buffer. Could not write memory buffer.")
        return

    def release(self):
        ndi.send_destroy(self.ndi_send)
