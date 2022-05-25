# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Spout",
    "author" : "Martin Froehlich",
    "description" : "Streaming Spout from Blender",
    "blender" : (3, 0, 0),
    "version" : (3, 0, 0),
    "location" : "Properties > Camera > Camera data",
    "warning" : "Experimental",
    "category" : "Render", 
    "wiki_url" : "https://github.com/maybites/blender.script.spout",
    "tracker_url" : "https://github.com/maybites/blender.script.spout/issues",
    "support" : "COMMUNITY"
}

import bpy

from . import (
    pip_importer
)

pip_importer.execute()

from . import (
    operators,
    ui,
)

from tempfile import gettempdir
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

# Clear handlers
if logger.hasHandlers():
    logger.handlers.clear()

logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(name)s:{%(levelname)s}: %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

filepath = Path(gettempdir()) / (__name__ + ".log")

logger.info("Logging into: " + str(filepath))
file_handler = logging.FileHandler(filepath, mode="w")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_prefs():
    return bpy.context.preferences.addons[__package__].preferences

def update_logger():
    prefs = get_prefs()
    #logger.setLevel(prefs.logging_level)

def register():
    # Register base
    update_logger()
    pip_importer.register()
    
    logger.info(
        "Enabled Spout GL, version: {}".format(bl_info["version"])
    )

    # Check Module and register all modules
    try:
        pip_importer.check_module()
        logger.info("SpoutGL available, fully registered modules")
    except ModuleNotFoundError:
        logger.warning(
            "SpoutGL module isn't available, only base modules registered"
        )


def unregister():
    pip_importer.unregister()

if __name__ == "__main__":
    register()
