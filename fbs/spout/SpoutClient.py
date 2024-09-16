from typing import Optional, Any

import SpoutGL
from io import BytesIO
import array
from itertools import repeat

import bpy
import logging

import time

from ..FrameBufferSharingClient import FrameBufferSharingClient


def make_empty_buffer(width, height, format):
    return BytesIO(
        bytes(repeat(0, width * height * SpoutGL.helpers.getBytesPerPixel(format)))
    )


GL_RGBA = SpoutGL.enums.GL_RGBA


class SpoutClient(FrameBufferSharingClient):
    def __init__(self, name: str = "SpoutClient"):
        super().__init__(name)
        self.sender_name = name
        self.receiver: Optional[SpoutGL.SpoutReceiver] = None

    def setup(self, sources):
        print("SpoutClient setup sources", sources)
        self.receiver = SpoutGL.SpoutReceiver()
        self.receiver.setReceiverName(self.sender_name)
        self.byte_buffer = None
        self.float_buffer = None

    def has_new_frame(self):
        return self.receiver.isFrameNew()

    def new_frame_image(self):
        # self.receiver.isFrameNew()
        return True

    def apply_frame_to_image(self, target_image: bpy.types.Image):
        # with SpoutGL.SpoutReceiver() as receiver:
        # self.receiver = receiver
        receiver = self.receiver

        sender_info = receiver.getSenderInfo(self.sender_name)
        width, height = sender_info.width, sender_info.height

        if (
            target_image.size[1] != height or
            target_image.size[0] != width or
            self.byte_buffer == None
        ):
            # Rescale blender image
            target_image.scale(width, height)
            # Update buffers dims
            self.float_buffer = array.array("f", repeat(0, width * height * 4))
            self.byte_buffer = make_empty_buffer(width, height, GL_RGBA)

        try:
            done = False
            while not done:
                result = receiver.receiveImage(
                    self.byte_buffer.getbuffer() if self.byte_buffer else None,
                    GL_RGBA,
                    False,
                    0,
                )
                if result:
                    if receiver.isUpdated():
                        # incoming_width = receiver.getSenderWidth()
                        # incoming_height = receiver.getSenderHeight()
                        # buffer = make_empty_buffer(incoming_width, incoming_height, GL_RGBA)
                        # # additions
                        # self.float_buffer = array.array(
                        #     "f", repeat(0, incoming_width * incoming_height * 4)
                        # )
                        # target_image.scale(incoming_width, incoming_height)
                        continue
                    # received_pixels = buffer.getvalue()
                    # Not sure why first frame is empty
                    if SpoutGL.helpers.isBufferEmpty(self.byte_buffer.getbuffer()):
                        continue
                    done = True

            # print("trying to get bytes, look for Got Bytes message just below",
            #     "isBufferEmpty",
            #     SpoutGL.helpers.isBufferEmpty(buffer.getbuffer()),
            # )
            # if (
            #     buffer and result and not SpoutGL.helpers.isBufferEmpty(buffer)
            # ):
            #     print("Got bytes", bytes(buffer[0:64]), "...")

            # Copy float buffer to image
            SpoutGL.helpers.copyToFloat32(self.byte_buffer.getbuffer(), self.float_buffer)
            target_image.pixels.foreach_set(self.float_buffer)

            # Per https://blenderartists.org/t/faster-image-pixel-data-access/1161411/6 faster than image.pixels =
            # when using a buffer
            # other example: target_image.pixels = (self.video_frame.data.flatten() / 255.0).astype(float)
            #
            # Make sure image gets marked dirty for rendering
            # target_image.update()
            # target_image.update_tag()

        except BufferError:
            pass

    def can_memory_buffer(self):
        return False

    def create_memory_buffer(self, texture_name: str, size: int):
        success = self.ctx.createMemoryBuffer(texture_name, size)

        if not success:
            logging.warning("Could not create memory buffer.")

        return

    def read_memory_buffer(self, texture_name: str, buffer):
        success = self.ctx.readMemoryBuffer(texture_name, buffer, len(buffer))

        if not success:
            logging.warning("Could not write memory buffer.")

        return

    def release(self):
        self.receiver.releaseReceiver()
