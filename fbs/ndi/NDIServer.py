import logging
from typing import Optional

import numpy as np
from cyndilib.sender import Sender
from cyndilib.video_frame import VideoSendFrame
from cyndilib.wrapper.ndi_structs import FourCC

import gpu
from gpu_extras.presets import draw_texture_2d

from ..FrameBufferSharingServer import FrameBufferSharingServer

class NDIServer(FrameBufferSharingServer):
    def __init__(self, name: str = "NDIServer"):
        super().__init__(name)
        self.sender = None
        self.video_frame = None
        self.width = 1920
        self.height = 1080

    def setup(self):
        # Create sender with the specified name
        self.sender = Sender(self.name)
        
        # Create and configure video frame
        self.video_frame = VideoSendFrame()
        self.video_frame.set_fourcc(FourCC.RGBA)
        self.video_frame.set_resolution(self.width, self.height)
        
        # Add video frame to sender
        self.sender.set_video_frame(self.video_frame)
        
        # Pre-allocate bytearray and memoryview for frame data
        frame_size_bytes = self.video_frame.get_data_size()
        self.frame_buffer = bytearray(frame_size_bytes)
        self.frame_view = memoryview(self.frame_buffer)
        
        # Start the sender
        self.sender.__enter__()

    def draw_texture(self, offscreen: gpu.types.GPUOffScreen, rect_pos: tuple[int, int], width: int, height: int):
        draw_texture_2d(offscreen.texture_color, rect_pos, width, height)

    def send_texture(self, offscreen: gpu.types.GPUOffScreen, width: int, height: int, is_flipped: bool = False):
        if not self.sender:
            return

        # Get texture from offscreen
        texture = offscreen.texture_color
        
        # Update dimensions if changed
        if (texture.height != self.height or texture.width != self.width):
            self.height = texture.height
            self.width = texture.width
            
            # Close sender before updating video frame
            self.sender.__exit__(None, None, None)
            
            # Recreate video frame with new dimensions
            self.video_frame = VideoSendFrame()
            self.video_frame.set_fourcc(FourCC.RGBA)
            self.video_frame.set_resolution(self.width, self.height)
            self.sender.set_video_frame(self.video_frame)
            
            # Re-allocate buffer for new size
            frame_size_bytes = self.video_frame.get_data_size()
            self.frame_buffer = bytearray(frame_size_bytes)
            self.frame_view = memoryview(self.frame_buffer)
            
            # Reopen sender
            self.sender.__enter__()
        
        # Get texture data and ensure proper format
        texture_data = texture.read()
        

        # Safely convert to numpy
        flat_np = self.safe_buffer_to_numpy(texture_data, self.height, self.width)

        # Convert to numpy array and ensure correct format
        # Reshape to match the expected dimensions (height, width, channels)
        # flat_np = np.array(texture_data, dtype=np.uint8)
        # flat_rs = flat_np.reshape((self.width, self.height, 4))
        
        # If texture is flipped, flip it vertically
        if is_flipped:
            flat_np = np.flipud(flat_np)
                    
        # Ensure memory is contiguous in case NDI expects tightly packed buffer
        flat_as = np.ascontiguousarray(flat_np)

        flat_tobytes = flat_as.tobytes()

        # Copy data into memoryview
        self.frame_view[:] = flat_tobytes
        
        # Send the frame
        self.sender.write_video_async(self.frame_view)

    def can_memory_buffer(self):
        return True

    def create_memory_buffer(self, texture_name: str, size: int):
        logging.warning("ndi does not support memory buffer. Could not create memory buffer.")
        return

    def write_memory_buffer(self, texture_name: str, buffer):
        logging.warning("syphon does not support memory buffer. Could not write memory buffer.")
        return

    def release(self):
        if self.sender:
            self.sender.__exit__(None, None, None)

    def safe_buffer_to_numpy(self, buffer, height, width, channels=4, dtype=np.uint8):
        """
        Safely converts a 3D gpu.types.Buffer to a NumPy array.
        
        Args:
            buffer: The gpu.types.Buffer object (shape: height x width x channels)
            height: The height of the image
            width: The width of the image
            channels: Number of channels (usually 4 for RGBA)
            dtype: NumPy data type, usually np.uint8 for UBYTE buffers
        
        Returns:
            np.ndarray of shape (height, width, channels), dtype=dtype
        """
        result = np.empty((height, width, channels), dtype=dtype)
        
        for y in range(height):
            for x in range(width):
                result[y, x] = buffer[y][x]

        return result