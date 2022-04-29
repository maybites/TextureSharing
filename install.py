import bpy
from . import (
    functions,
    global_data,
    operators,
    ui,
)
from bpy.types import Operator

modules = (
    operators,
    ui,
)



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

        global_data.registered = True
        register_full()
    except ModuleNotFoundError as e:
        global_data.registered = False
        raise e


class View3D_OT_SpoutGL_install_package(Operator):
    """Install module from local .whl file or from PyPi"""

    bl_idname = "view3d.spoutgl_install_package"
    bl_label = "Install"

    package: bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return not global_data.registered

    def execute(self, context):
        if not functions.ensure_pip():
            self.report(
                {"WARNING"},
                "PIP is not available and cannot be installed, please install PIP manually",
            )
            return {"CANCELLED"}

        if not self.package:
            self.report({"WARNING"}, "Specify package to be installed")
            return {"CANCELLED"}

        if functions.install_package(self.package):
            try:
                check_module()
                self.report({"INFO"}, "Package successfully installed")
            except ModuleNotFoundError:
                self.report({"WARNING"}, "Package should be available but cannot be found, check console for detailed info. Try restarting blender, otherwise get in contact.")
            functions.show_package_info("SpoutGL")
        else:
            self.report({"WARNING"}, "Cannot install package: {}".format(self.package))
            return {"CANCELLED"}
        return {"FINISHED"}


def register():
    bpy.utils.register_class(View3D_OT_SpoutGL_install_package)


def unregister():
    bpy.utils.unregister_class(View3D_OT_SpoutGL_install_package)