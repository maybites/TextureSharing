from typing import Optional
from dataclasses import dataclass
import bpy

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
    install_manualy: bool = False
    _registered: bool = False
    _summary: str = ""
    _home_page: str = ""
    _author: str = ""
    _license: str = ""
    _location: str = ""
    
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
        module = sys.modules[package.module]
        if hasattr(module, '__path__'):
            package._location = module.__path__[0]
            package._registered = True

    except KeyError:
        package._registered = False
        try:
            # check if the module can be properly imported..
            __import__(package.module)

            get_package_show(package)
                    
        except ModuleNotFoundError:
            pass

    return package._registered  


def get_package_show(package):
    try:
        cmd = [PYPATH, "-m", "pip", "show",  package.name]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        store_package_show(package, result)
    except:
        pass

def store_package_show(package, result):
    # Initialize an empty dictionary
    data = {}

    # Split the output into lines and parse each line
    for line in result.stdout.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)  # Only split on the first occurrence
            data[key.strip()] = value.strip()
    
    if len(data) > 0:
        # there seems to be a valid module installed
        package._summary = data.get('Summary')
        package._home_page = data.get('Home-page')
        package._author = data.get('Author')
        package._license = data.get('License')
        package._location = data.get('Location')  
        package._registered = True

        return True
    
    return False

def check_modules():
    # Note: Blender might be installed in a directory that needs admin rights and thus defaulting to a user installation.
    # That path however might not be in sys.path....
    for package in pip_packages:
        check_module(package)

def get_prefs():
    return bpy.context.preferences.addons[__package__].preferences

def install_pip():
    cmd = [PYPATH, "-m", "ensurepip", "--upgrade"]
    return not subprocess.call(cmd)


def update_pip():
    cmd = [PYPATH, "-m", "pip", "install", "--upgrade", "pip"]
    return not subprocess.call(cmd)

def install_package(package, file_path):
    update_pip()
    if package.install_manualy:
        cmd = [PYPATH, "-m", "pip", "install", "--upgrade", file_path]
        ok = subprocess.call(cmd) == 0
    else:
        cmd = [PYPATH, "-m", "pip", "install", "--upgrade", f"{package.name}{package.version}"]
        ok = subprocess.call(cmd) == 0
    return ok

def uninstall_package(package):
    update_pip()
    cmd = [PYPATH, "-m", "pip", "uninstall", "-y", package.name]
    ok = subprocess.call(cmd) == 0
    package._registered = False
    return ok

def ensure_pip():
    if subprocess.call([PYPATH, "-m", "pip", "--version"]):
        return install_pip()
    return True

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
def get_scale():
    return bpy.context.preferences.system.ui_scale * get_prefs().entity_scale

def is_experimental():
    return get_prefs().show_debug_settings

class PiPPreferences(AddonPreferences):
    bl_idname = __package__
    bl_label = "pip installer"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        system = context.preferences.system
        scene = context.scene
        spout_addon_props = scene.spout_addon_props

        allInstalled = True

        if just_imported:
            box = layout.box()
            row = box.row()
            box.label(text="Restart the addon to make it functional!", icon="ERROR")

        # layout.label(text="Ideal setting for usage of texture sharing is: Single pass Anti-Aliasing")
        # layout.prop(system, "viewport_aa")
 
        for package in pip_packages:
            box = layout.box()
            box.label(text=package.name)
            row = box.row().split(factor=0.2)
            if package._registered:
                row.label(text="Registered", icon="CHECKMARK")
                row.label(text=package._location)
                row.operator(
                    Pip_Uninstall_package.bl_idname,
                    text="uninstall",
                ).package_path=package.name
            else:
                allInstalled = False
                row.label(text="Not installed", icon="CANCEL")
                if package.install_manualy:
                    row.prop(spout_addon_props, 'my_file_path')
                row.operator(
                        Pip_Install_packages.bl_idname,
                        text="install"
                    ).package_path=package.name

# Refresh operator
class Pip_Update_package(Operator):
    """refresh module from local .whl file or from PyPi"""

    bl_idname = "view3d.pip_refresh_package"
    bl_label = "Install"

    package_path: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        spout_addon_props = scene.spout_addon_props

        package = {e.name: e for e in pip_packages}[str(self.package_path)]

        if not self.package_path:
            self.report({"WARNING"}, "Specify package to be installed")
            return {"CANCELLED"}

        if install_package(package, spout_addon_props.my_file_path):
            self.report({"INFO"}, "Testing Package {} import..".format(package.module))
            if check_module(package):
                self.report({"INFO"}, "Package successfully installed")
            else:
                self.report({"WARNING"}, "Package should be available but cannot be found, check console for detailed info. Try restarting blender, otherwise get in contact.")
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

    package_path: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        spout_addon_props = scene.spout_addon_props
    
        if not ensure_pip():
            self.report(
                {"WARNING"},
                "PIP is not available and cannot be installed, please install PIP manually",
            )
            return {"CANCELLED"}

        package = {e.name: e for e in pip_packages}[str(self.package_path)]

        if install_package(package, spout_addon_props.my_file_path):
            self.report({"INFO"}, "Testing Package {} import..".format(package.module))
            if check_module(package):
                self.report({"INFO"}, "Package successfully installed")
            else:
                self.report({"WARNING"}, "Package should be available but cannot be found, check console for detailed info. Try restarting blender, otherwise get in contact.")
        else:
            self.report({"WARNING"}, "Cannot install package: {}".format(self.package_path))
        
        global just_imported
        just_imported = True

        return {"FINISHED"}

class SpoutAddonProperties(bpy.types.PropertyGroup):
    # Define a StringProperty for the filepath
    my_file_path: bpy.props.StringProperty(
        name="Wheel file",
        description="Path to the file",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'  # This subtype turns the StringProperty into a file picker
    )
 

classes =     (
    Pip_Update_package,
    Pip_Uninstall_package,
    Pip_Install_packages,
    PiPPreferences,
    SpoutAddonProperties
)

def register():
    global pip_packages
    pip_packages.clear()

    global just_imported
    just_imported = False

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    bpy.types.Scene.spout_addon_props = bpy.props.PointerProperty(type=SpoutAddonProperties)


def unregister():
    del bpy.types.Scene.spout_addon_props
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)