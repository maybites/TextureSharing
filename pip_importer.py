from typing import Optional
from numpy import append
from dataclasses import dataclass
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

@dataclass
class Package:
    name: str
    custom_module: Optional[str] = None
    version: str = ""
    _registered: bool = False

    @property
    def module(self) -> str:
        if self.custom_module is None:
            return self.name
        return self.custom_module


def check_module():
    # Note: Blender might be installed in a directory that needs admin rights and thus defaulting to a user installation.
    # That path however might not be in sys.path....
    import sys, site, importlib

    p = site.USER_SITE
    if p not in sys.path:
        sys.path.append(p)
    for package in pip_packages:
        try:
            __import__(package.module)

            import importlib
            package._registered = True
        except ModuleNotFoundError as e:
            package._registered = False
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
    cmd = [PYPATH, "-m", "pip", "install", "--upgrade", f"{package.name}{package.version}"]
    ok = subprocess.call(cmd) == 0
    return ok


def ensure_pip():
    if subprocess.call([PYPATH, "-m", "pip", "--version"]):
        return install_pip()
    return True


def show_package_info(package):
    try:
        subprocess.call([PYPATH, "-m", "pip", "show", package.name])
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

        for package in pip_packages:
            box = layout.box()
            box.label(text=package.name)
            row = box.row().split(factor=0.2)
            if package._registered:
                row.label(text="Registered", icon="CHECKMARK")
                module = sys.modules[package.module]
                row.label(text="Path: " + module.__path__[0])
                row.operator(
                    Pip_Install_package.bl_idname,
                    text="refresh",
                ).package_path=package.name
            else:
                row.label(text="NotFound", icon="CANCEL")
                row.operator(
                    Pip_Install_package.bl_idname,
                    text="Install from PIP"
                ).package_path=package.name

# installation operator
class Pip_Install_package(Operator):
    """Install module from local .whl file or from PyPi"""

    bl_idname = "view3d.pip_install_package"
    bl_label = "Install"

    package_path: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        package = {e.name: e for e in pip_packages}[str(self.package_path)]

        if not ensure_pip():
            self.report(
                {"WARNING"},
                "PIP is not available and cannot be installed, please install PIP manually",
            )
            return {"CANCELLED"}

        if not self.package_path:
            self.report({"WARNING"}, "Specify package to be installed")
            return {"CANCELLED"}

        if install_package(package):
            try:
                check_module()
                self.report({"INFO"}, "Package successfully installed")
            except ModuleNotFoundError:
                self.report({"WARNING"}, "Package should be available but cannot be found, check console for detailed info. Try restarting blender, otherwise get in contact.")
            show_package_info(package)
        else:
            self.report({"WARNING"}, "Cannot install package: {}".format(self.package_path))
            return {"CANCELLED"}
        return {"FINISHED"}


classes =     (
    Pip_Install_package,
    PiPPreferences
)

def register(*packages):
    global pip_packages
    pip_packages = packages

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)