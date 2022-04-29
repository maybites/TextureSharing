import bpy
from . import global_data
import subprocess


def get_prefs():
    return bpy.context.preferences.addons[__package__].preferences


def install_pip():
    cmd = [global_data.PYPATH, "-m", "ensurepip", "--upgrade"]
    return not subprocess.call(cmd)


def update_pip():
    cmd = [global_data.PYPATH, "-m", "pip", "install", "--upgrade", "pip"]
    return not subprocess.call(cmd)


def install_package(package):
    update_pip()
    cmd = [global_data.PYPATH, "-m", "pip", "install", "--upgrade"] + package.split(" ")
    ok = subprocess.call(cmd) == 0
    return ok


def ensure_pip():
    if subprocess.call([global_data.PYPATH, "-m", "pip", "--version"]):
        return install_pip()
    return True


def show_package_info(package):
    try:
        subprocess.call([global_data.PYPATH, "-m", "pip", "show", package])
    except:
        pass


# NOTE: this is currently based on the enum_items list,
# alternatively this could also work on registered EnumProperties
class bpyEnum:
    """Helper class to interact with bpy enums"""

    def __init__(self, data, index=None, identifier=None):
        self.data = data

        if not identifier:
            self.identifier = self._get_identifier(index)
        else:
            self.identifier = identifier
        item = self._get_active_item()

        self.name = item[1]
        self.description = item[2]
        self.index = item[-1]
        if len(item) == 5:
            icon = item[3]
        else:
            icon = None
        self.icon = icon

    def _get_active_item(self):
        i = [item[0] for item in self.data].index(self.identifier)
        return self.data[i]

    def _get_item_index(self, item):
        if len(item) > 3:
            return item[-1]
        return self.data.index(item)

    def _get_identifier(self, index):
        i = [self._get_item_index(item) for item in self.data].index(index)
        return self.data[i][0]

