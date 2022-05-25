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

import sys
import subprocess
import logging
from pathlib import Path

PYPATH = sys.executable
registered = False

# separate packages with spaces
pip_packages = "SpoutGL" 

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


def execute():
    if not ensure_pip():
        logger.info("CANCELLED")

    if install_package(pip_packages):
        try:
            check_module()
            logger.info("Package successfully installed")
        except ModuleNotFoundError:
            logger.info("Package should be available but cannot be found, check console for detailed info. Try restarting blender, otherwise get in contact.")
        show_package_info("SpoutGL")
    else:
        logger.info("Cannot install package: {}".format(pip_packages))
        logger.info("CANCELLED")
    logger.info("FINISHED")

def register_full():
    for m in modules:
        m.register()

def unregister_full():
    for m in reversed(modules):
        m.unregister()

def check_module():
    # Note: Blender might be installed in a directory that needs admin rights and thus defaulting to a user installation.
    # That path however might not be in sys.path....
    import sys, site

    p = site.USER_SITE
    if p not in sys.path:
        sys.path.append(p)
    try:
        import SpoutGL

        registered = True
        register_full()
    except ModuleNotFoundError as e:
        registered = False
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

        box = layout.box()
        box.label(text="Spout Module")
        if registered:
            box.label(text="Registered", icon="CHECKMARK")
            module = sys.modules["SpoutGL"]
            box.label(text="Path: " + module.__path__[0])
        else:
            row = box.row()
            row.label(text="Module isn't Registered", icon="CANCEL")


classes =     (
    PiPPreferences,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)