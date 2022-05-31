from numpy import append
import bpy
from bpy.props import (
    PointerProperty,
    BoolProperty,
    StringProperty,
    EnumProperty,
    IntProperty,
    FloatProperty
)

from bpy.types import AddonPreferences, Panel, Menu
from bpy.types import Operator

import sys
import subprocess
import logging
from pathlib import Path

PYPATH = sys.executable

# separate packages with spaces
pip_packages = []
pip_packages_reg = []

log_levels = [
    ("CRITICAL", "Critical", "", 0),
    ("ERROR", "Error", "", 1),
    ("WARNING", "Warning", "", 2),
    ("INFO", "Info", "", 3),
    ("DEBUG", "Debug", "", 4),
    ("NOTSET", "Notset", "", 5),
]

logger = logging.getLogger(__name__)

def get_log_level(self):
    prop = self.bl_rna.properties["logging_level"]
    items = prop.enum_items
    default_value = items[prop.default].value
    item = items[self.get("logging_level", default_value)]
    return item.value


def check_module():
    # Note: Blender might be installed in a directory that needs admin rights and thus defaulting to a user installation.
    # That path however might not be in sys.path....
    import sys, site, importlib
    global pip_packages_reg

    p = site.USER_SITE
    if p not in sys.path:
        sys.path.append(p)
    for i in range(len(pip_packages)):
        package = pip_packages[i]
        try:
            __import__(package)
            pip_packages_reg[i] = True
        except ModuleNotFoundError as e:
            pip_packages_reg[i] = False
            raise e


def get_prefs():
    return bpy.context.preferences.addons[__package__].preferences


def install_pip():
    cmd = [PYPATH, "-m", "ensurepip", "--upgrade"]
    return not subprocess.call(cmd)


def update_pip():
    cmd = [PYPATH, "-m", "pip", "install", "--upgrade", "pip"]
    return not subprocess.call(cmd)


def install_package(package):
    update_pip()
    cmd = [PYPATH, "-m", "pip", "install", "--upgrade"] + package.split(" ")
    ok = subprocess.call(cmd) == 0
    return ok


def ensure_pip():
    if subprocess.call([PYPATH, "-m", "pip", "--version"]):
        return install_pip()
    return True


def show_package_info(package):
    try:
        subprocess.call([PYPATH, "-m", "pip", "show", package])
    except:
        pass

def get_wheel():
    p = Path(__file__).parent.absolute()
    from sys import platform, version_info

    if platform == "linux" or platform == "linux2":
        # Linux
        platform_strig = "linux"
    elif platform == "darwin":
        # OS X
        platform_strig = "macosx"
    elif platform == "win32":
        # Windows
        platform_strig = "win"

    matches = list(
        p.glob(
            "**/*cp{}{}*{}*.whl".format(
                version_info.major, version_info.minor, platform_strig
            )
        )
    )
    if matches:
        match = matches[0]
        logger.info("Local installation file available: " + str(match))
        return match.as_posix()
    return ""


### Presets
from bl_ui.utils import PresetPanel

def get_scale():
    return bpy.context.preferences.system.ui_scale * get_prefs().entity_scale

def is_experimental():
    return get_prefs().show_debug_settings


class PiPPreferences(AddonPreferences):
    bl_idname = __package__

    package_path: StringProperty(
        name="Package Filepath",
        description="Filepath to the module's .whl file",
        subtype="FILE_PATH",
        default=get_wheel(),
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        for i in range(len(pip_packages)):
            package = pip_packages[i]

            box = layout.box()
            box.label(text=package)
            row = box.row().split(factor=0.2)
            if pip_packages_reg[i] :
                row.label(text="Registered", icon="CHECKMARK")
                module = sys.modules[package]
                row.label(text="Path: " + module.__path__[0])
                row.operator(
                    Pip_Install_package.bl_idname,
                    text="refresh",
                ).package = package
            else:
                row.label(text="NotFound", icon="CANCEL")
                row.operator(
                    Pip_Install_package.bl_idname,
                    text="Install from PIP",
                ).package = package

# installation operator
class Pip_Install_package(Operator):
    """Install module from local .whl file or from PyPi"""

    bl_idname = "view3d.pip_install_package"
    bl_label = "Install"

    package: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        if not ensure_pip():
            self.report(
                {"WARNING"},
                "PIP is not available and cannot be installed, please install PIP manually",
            )
            return {"CANCELLED"}

        if not self.package:
            self.report({"WARNING"}, "Specify package to be installed")
            return {"CANCELLED"}

        if install_package(self.package):
            try:
                check_module()
                self.report({"INFO"}, "Package successfully installed")
            except ModuleNotFoundError:
                self.report({"WARNING"}, "Package should be available but cannot be found, check console for detailed info. Try restarting blender, otherwise get in contact.")
            show_package_info(self.package)
        else:
            self.report({"WARNING"}, "Cannot install package: {}".format(self.package))
            return {"CANCELLED"}
        return {"FINISHED"}


classes =     (
    Pip_Install_package,
    PiPPreferences,
)

def register(packages):
    global pip_packages
    pip_packages = packages

    for package in pip_packages:
        pip_packages_reg.append(False)

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)