import sys
from enum import Enum
from mathutils import Vector

registered = False

PYPATH = sys.executable

entities = {}
batches = {}

offscreen = None
redraw_selection_buffer = False
