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
    "author" : "Martin Froehlich, Florian Bruggisser",
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

import platform

from . import (
    pip_importer,
)

def register():
    # First startup the pip importer
    pip_importer.register()

    # then add the required packages
    if platform.system() == "Windows":
        pip_importer.add_package(pip_importer.Package("SpoutGL", version="==0.0.4"))

    if platform.system() == "Darwin":  
        pip_importer.add_package(pip_importer.Package("syphonpy", version="==0.0.2"))

    # pip_importer.auto_install_packages()

    # Check required modules availability
    try:
        pip_importer.check_modules()

        from . import operators, ui
        operators.register()
        ui.register()
    except ModuleNotFoundError:
        print(
            "Addon isn't available, install required module via Properties > Addons > Spout"
        )


def unregister():
    try:
        operators.unregister()
        ui.unregister()
    except Exception:
        pass

    pip_importer.unregister()

if __name__ == "__main__":
    register()
