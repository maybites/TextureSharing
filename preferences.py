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
from pathlib import Path
import logging

from . import functions, global_data, install


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


def set_log_level(self, value):
    items = self.bl_rna.properties["logging_level"].enum_items
    item = items[value]

    level = item.identifier
    logger.info("setting log level: {}".format(item.name))
    self["logging_level"] = level
    logger.setLevel(level)

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



def get_prefs():
    return bpy.context.preferences.addons[__package__].preferences

def get_scale():
    return bpy.context.preferences.system.ui_scale * get_prefs().entity_scale

def is_experimental():
    return get_prefs().show_debug_settings


class SpoutPreferences(AddonPreferences):
    bl_idname = __package__

    show_debug_settings: BoolProperty(
        name="Show Debug Settings",
        default=False,
    )
    package_path: StringProperty(
        name="Package Filepath",
        description="Filepath to the module's .whl file",
        subtype="FILE_PATH",
        default=get_wheel(),
    )
    logging_level: EnumProperty(
        name="Logging Level",
        items=log_levels,
        get=get_log_level,
        set=set_log_level,
        default=2,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        box = layout.box()
        box.label(text="Spout Module")
        if global_data.registered:
            box.label(text="Registered", icon="CHECKMARK")
            module = sys.modules["SpoutGL"]
            box.label(text="Path: " + module.__path__[0])
        else:
            row = box.row()
            row.label(text="Module isn't Registered", icon="CANCEL")
            split = box.split(factor=0.8)
            split.prop(self, "package_path", text="")
            split.operator(
                install.View3D_OT_SpoutGL_install_package.bl_idname,
                text="Install from File",
            ).package = self.package_path

            row = box.row()
            row.operator(
                install.View3D_OT_SpoutGL_install_package.bl_idname,
                text="Install from PIP",
            ).package = "SpoutGL"


classes =     (
    SpoutPreferences,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)