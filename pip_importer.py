from typing import Optional
from dataclasses import dataclass
import bpy
from bpy.props import (
    StringProperty,
)

from bpy.types import AddonPreferences, Panel, Menu
from bpy.types import Operator
import addon_utils

import sys
import subprocess
from pathlib import Path

PYPATH = sys.executable

# separate packages with spaces
pip_packages = []

# flag to indicate if the required packages were imported in this session 
just_imported = False

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

def add_package(package):
    pip_packages.append(package)

def auto_install_packages():
    for package in pip_packages:
        try:
            check_module(package)
            if not package._registered:
                install_package(package)
        except ModuleNotFoundError as e:
            pass         

def check_module(package):
    # Note: Blender might be installed in a directory that needs admin rights and thus defaulting to a user installation.
    # That path however might not be in sys.path....
    import sys, site

    p = site.USER_SITE
    if p not in sys.path:
        sys.path.append(p)
    try:
        __import__(package.module)

        package._registered = True
    except ModuleNotFoundError as e:
        package._registered = False
        raise e

def check_modules():
    # Note: Blender might be installed in a directory that needs admin rights and thus defaulting to a user installation.
    # That path however might not be in sys.path....
    import sys, site

    p = site.USER_SITE
    if p not in sys.path:
        sys.path.append(p)
    for package in pip_packages:
        try:
            __import__(package.module)

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

def uninstall_package(package):
    update_pip()
    cmd = [PYPATH, "-m", "pip", "uninstall", "-y", package.name]
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
    bl_label = "pip installer"

    package_path: StringProperty(
        name="Package Filepath",
        description="Filepath to the module's .whl file",
        subtype="FILE_PATH",
        default=get_wheel(),
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        allInstalled = True

        for package in pip_packages:
            box = layout.box()
            box.label(text=package.name)
            row = box.row().split(factor=0.2)
            if package._registered:
                row.label(text="Registered", icon="CHECKMARK")
                module = sys.modules[package.module]
                if hasattr(module, '__path__'):
                    row.label(text="Path: " + module.__path__[0])
                row.operator(
                    Pip_Refresh_package.bl_idname,
                    text="refresh",
                ).package_path=package.name
                row.operator(
                    Pip_Uninstall_package.bl_idname,
                    text="uninstall",
                ).package_path=package.name
            else:
                allInstalled = False
                row.label(text="NotFound", icon="CANCEL")
                
        if  allInstalled is False:    
            box = layout.box()
            row = box.row()
            row.operator(
                    Pip_Install_packages.bl_idname,
                    text="Install from PIP"
                )

        if just_imported:
            box = layout.box()
            row = box.row()
            box.label(text="Restart the addon to make it functional!", icon="ERROR")

# Refresh operator
class Pip_Refresh_package(Operator):
    """refresh module from local .whl file or from PyPi"""

    bl_idname = "view3d.pip_refresh_package"
    bl_label = "Install"

    package_path: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        package = {e.name: e for e in pip_packages}[str(self.package_path)]

        if not self.package_path:
            self.report({"WARNING"}, "Specify package to be installed")
            return {"CANCELLED"}

        if install_package(package):
            try:
                check_module(package)
                self.report({"INFO"}, "Package successfully installed")
            except ModuleNotFoundError:
                self.report({"WARNING"}, "Package should be available but cannot be found, check console for detailed info. Try restarting blender, otherwise get in contact.")
            show_package_info(package)
        else:
            self.report({"WARNING"}, "Cannot install package: {}".format(self.package_path))
            return {"CANCELLED"}
        return {"FINISHED"}

# Uninstall operator
class Pip_Uninstall_package(Operator):
    """uninstall module from local .whl file or from PyPi"""

    bl_idname = "view3d.pip_uninstall_package"
    bl_label = "Uninstall"

    package_path: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        package = {e.name: e for e in pip_packages}[str(self.package_path)]

        if not self.package_path:
            self.report({"WARNING"}, "Specify package to be uninstalled")
            return {"CANCELLED"}

        if uninstall_package(package):
            package._registered = False
            self.report({"INFO"}, "Package successfully uninstalled")
        else:
            self.report({"WARNING"}, "Cannot uninstall package: {}".format(self.package_path))
            return {"CANCELLED"}
        return {"FINISHED"}


# installation operator
class Pip_Install_packages(Operator):
    """Install modules from local .whl file or from PyPi"""

    bl_idname = "view3d.pip_install_packages"
    bl_label = "Install"

    def execute(self, context):
        if not ensure_pip():
            self.report(
                {"WARNING"},
                "PIP is not available and cannot be installed, please install PIP manually",
            )
            return {"CANCELLED"}

        for package in pip_packages:
            if install_package(package):
                try:
                    check_module(package)
                    self.report({"INFO"}, "Package successfully installed")
                except ModuleNotFoundError:
                    self.report({"WARNING"}, "Package should be available but cannot be found, check console for detailed info. Try restarting blender, otherwise get in contact.")
                show_package_info(package)
            else:
                self.report({"WARNING"}, "Cannot install package: {}".format(self.package_path))
        
        global just_imported
        just_imported = True

        return {"FINISHED"}


classes =     (
    Pip_Refresh_package,
    Pip_Uninstall_package,
    Pip_Install_packages,
    PiPPreferences
)

def register():
    global pip_packages
    pip_packages.clear()

    global just_imported
    just_imported = False

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)