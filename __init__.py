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
    "name" : "TextureSharing",
    "author" : "Martin Froehlich, Florian Bruggisser",
    "description" : "Sharing Textures via Spout or Syphon from Blender",
    "blender" : (3, 0, 0),
    "version" : (4, 0, 0),
    "doc_url" : "https://github.com/maybites/blender-texture-sharing",
    "location" : "Properties > Camera > Camera data",
    "category" : "Render", 
    "wiki_url" : "https://github.com/maybites/blender-texture-sharing",
    "tracker_url" : "https://github.com/maybites/blender-texture-sharing/issues",
    "support" : "COMMUNITY"
}

import platform

from . import (
    pip_importer,
)

def register():
    # First startup the pip importer
    pip_importer.register()

    # then add the required packages
    if platform.system() == "Windows":
        pip_importer.add_package(pip_importer.Package("SpoutGL", version="==0.0.4", custom_module="SpoutGL"))

    if platform.system() == "Darwin":  
        pip_importer.add_package(pip_importer.Package("syphon-python", version="==0.1.0", custom_module="syphon"))

    # pip_importer.auto_install_packages()

    # Check required modules availability
    try:
        pip_importer.check_modules()

        from . import operators, ui, keys
        keys.register()
        operators.register()
        ui.register()
    except ModuleNotFoundError:
        print(
            "Addon isn't available, install required module via Properties > Addons > Spout"
        )


def unregister():
    try:
        from . import operators, ui, keys
        operators.unregister()
        ui.unregister()
        keys.unregister()
    except Exception:
        pass

    pip_importer.unregister()

if __name__ == "__main__":
    register()
