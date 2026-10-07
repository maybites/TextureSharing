from typing import Optional
from dataclasses import dataclass
import bpy

from bpy.types import AddonPreferences, Panel, Menu
from bpy.types import Operator
import addon_utils

import sys
import subprocess
import threading
import time
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
    _installed_version: str = ""

    @property
    def module(self) -> str:
        if self.custom_module is None:
            return self.name
        return self.custom_module

# comparison operators accepted in a package's version spec (e.g. "==0.1.1"),
# ordered so that two-character operators are matched before their prefix
_VERSION_OPERATORS = ("==", "!=", ">=", "<=", "~=", ">", "<")

def _parse_version_spec(spec):
    spec = spec.strip()
    for op in _VERSION_OPERATORS:
        if spec.startswith(op):
            return op, spec[len(op):].strip()
    return "==", spec

def _version_key(v):
    # best-effort numeric parse of a dotted version string, ignoring any
    # pre/post-release suffixes (e.g. "0.1.1rc1" -> (0, 1, 1))
    parts = []
    for chunk in v.split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)

def _version_satisfies(installed, spec):
    # returns whether the installed version string satisfies the package's
    # required version spec (e.g. "==0.1.1", ">=0.1.0"). An empty spec means
    # any installed version is acceptable.
    if not spec:
        return True
    if not installed:
        return False

    op, required = _parse_version_spec(spec)
    iv, rv = _version_key(installed), _version_key(required)

    if op == "==":
        return iv == rv
    if op == "!=":
        return iv != rv
    if op == ">=":
        return iv >= rv
    if op == "<=":
        return iv <= rv
    if op == ">":
        return iv > rv
    if op == "<":
        return iv < rv
    if op == "~=":
        return iv >= rv and iv[:-1] == rv[:-1]
    return iv == rv

def _get_installed_version(package):
    try:
        from importlib.metadata import version as pkg_version
        return pkg_version(package.name)
    except Exception:
        return ""

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
            package._installed_version = _get_installed_version(package)
            package._registered = _version_satisfies(package._installed_version, package.version)

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
    import subprocess
    import locale
    from sys import platform
    
    try:
        # Get the most appropriate encoding
        if platform == "win32":
            # Try to get console encoding, fall back to locale encoding
            import os
            enc = os.device_encoding(1) or locale.getpreferredencoding() or 'utf-8'
        else:
            enc = 'utf-8'
        
        cmd = [PYPATH, "-m", "pip", "show", package.name]
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            encoding=enc,
            errors='replace'  # Still use replace to prevent crashes
        )
        store_package_show(package, result)
    except subprocess.SubprocessError:
        # Handle subprocess-specific errors
        pass
    except Exception:
        # Handle other unexpected errors
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
        package._installed_version = data.get('Version', '')
        package._registered = _version_satisfies(package._installed_version, package.version)

        return package._registered

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

# pip runs in a worker thread so that Blender's UI stays responsive while
# packages are installed. The result is picked up on the main thread by a
# bpy.app.timers poll function, which is the only place touching bpy data.
class _PipJob:
    def __init__(self, kind, package, file_path=""):
        self.kind = kind  # "install" or "uninstall"
        self.package = package
        self.file_path = file_path
        self.step = ""
        self.ok = False
        self.error = ""
        self.done = False
        self.started = time.time()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        try:
            if self.kind == "install":
                self.step = "Preparing pip"
                if not ensure_pip():
                    self.error = "PIP is not available and cannot be installed, please install PIP manually"
                    return
                self.step = "Installing {}".format(self.package.name)
                self.ok = install_package(self.package, self.file_path)
            else:
                self.step = "Uninstalling {}".format(self.package.name)
                self.ok = uninstall_package(self.package)
        except Exception as e:
            self.error = str(e)
        finally:
            self.done = True

_job = None
# last finished job result as (message, is_error), shown in the preferences
_last_result = None

def is_busy():
    return _job is not None

def _redraw_all():
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()
    except Exception:
        pass

def start_job(kind, package, file_path=""):
    # returns False if another job is still running
    global _job, _last_result
    if _job is not None:
        return False
    _last_result = None
    _job = _PipJob(kind, package, file_path)
    _job.thread.start()
    bpy.context.window_manager.progress_begin(0, 100)
    bpy.app.timers.register(_poll_job, first_interval=0.25)
    _redraw_all()
    return True

def _poll_job():
    global _job, _last_result, just_imported
    job = _job
    if job is None:
        return None

    wm = bpy.context.window_manager
    if not job.done:
        # indeterminate progress indicator in the status bar
        wm.progress_update(int((time.time() - job.started) * 10) % 100)
        _redraw_all()
        return 0.25

    wm.progress_end()
    package = job.package
    if job.kind == "install":
        if job.ok:
            if check_module(package):
                _last_result = ("{} successfully installed".format(package.name), False)
            else:
                _last_result = ("{} should be available but cannot be found, check the console for details. Try restarting Blender.".format(package.name), True)
            just_imported = True
        else:
            _last_result = (job.error or "Cannot install package: {}".format(package.name), True)
    else:
        if job.ok:
            package._registered = False
            _last_result = ("{} successfully uninstalled".format(package.name), False)
        else:
            _last_result = (job.error or "Cannot uninstall package: {}".format(package.name), True)

    print("pip_importer: " + _last_result[0])
    _job = None
    _redraw_all()
    return None

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
 
        if _job is not None:
            box = layout.box()
            box.label(
                text="{}... {}s (Blender stays usable, please wait)".format(_job.step, int(time.time() - _job.started)),
                icon="TIME",
            )
        elif _last_result is not None:
            box = layout.box()
            box.label(text=_last_result[0], icon="ERROR" if _last_result[1] else "CHECKMARK")

        for package in pip_packages:
            box = layout.box()
            box.enabled = _job is None
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
                if package._installed_version:
                    row.label(
                        text="Outdated ({} -> {})".format(package._installed_version, package.version),
                        icon="CANCEL",
                    )
                else:
                    row.label(text="Not installed", icon="CANCEL")
                if package.install_manualy:
                    row.prop(spout_addon_props, 'my_file_path')
                row.operator(
                        Pip_Install_packages.bl_idname,
                        text="install"
                    ).package_path=package.name

def _start_from_operator(operator, kind, file_path=""):
    if not operator.package_path:
        operator.report({"WARNING"}, "Specify package to be {}".format("installed" if kind == "install" else "uninstalled"))
        return {"CANCELLED"}

    package = {e.name: e for e in pip_packages}[str(operator.package_path)]

    if not start_job(kind, package, file_path):
        operator.report({"WARNING"}, "Another package operation is still running")
        return {"CANCELLED"}

    operator.report({"INFO"}, "{} {} in the background...".format("Installing" if kind == "install" else "Uninstalling", package.name))
    return {"FINISHED"}

# Refresh operator
class Pip_Update_package(Operator):
    """refresh module from local .whl file or from PyPi"""

    bl_idname = "view3d.pip_refresh_package"
    bl_label = "Install"

    package_path: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        return _start_from_operator(self, "install", context.scene.spout_addon_props.my_file_path)

# Uninstall operator
class Pip_Uninstall_package(Operator):
    """uninstall module from local .whl file or from PyPi"""

    bl_idname = "view3d.pip_uninstall_package"
    bl_label = "Uninstall"

    package_path: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        return _start_from_operator(self, "uninstall")


# installation operator
class Pip_Install_packages(Operator):
    """Install modules from local .whl file or from PyPi"""

    bl_idname = "view3d.pip_install_packages"
    bl_label = "Install"

    package_path: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        return _start_from_operator(self, "install", context.scene.spout_addon_props.my_file_path)

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

    global just_imported, _job, _last_result
    just_imported = False
    _job = None
    _last_result = None

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    bpy.types.Scene.spout_addon_props = bpy.props.PointerProperty(type=SpoutAddonProperties)


def unregister():
    del bpy.types.Scene.spout_addon_props
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
