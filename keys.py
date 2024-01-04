import bpy

texsServerItems = {
    ("INPUT", "Input", "Receive the OSC message from somewhere else", "IMPORT", 0),
    ("OUTPUT", "Output", "Send the OSC message from this node", "EXPORT", 1),
    ("BOTH", "Both", "Send and Reveive this OSC message", "FILE_REFRESH", 2) }

class TEXS_MsgValues(bpy.types.PropertyGroup):
    #key_path = bpy.props.StringProperty(name="Key", default="Unknown")
    enabled: bpy.props.BoolProperty(name="Enabled", default=False)
    description: bpy.props.StringProperty(name="Description", default="Texture Receiver")
    texs_source: bpy.props.EnumProperty(name = "RX", items = texsServerItems)
    texs_image: bpy.props.PointerProperty(name="Image", type=bpy.types.Image)
    ui_expanded: bpy.props.BoolProperty(name="Expanded", default=True)

key_classes = (
    TEXS_MsgValues,
)

def register():
    for cls in key_classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.TEXS_keys = bpy.props.CollectionProperty(type=TEXS_MsgValues, description='collection of custom osc handler')


def unregister():
    del bpy.types.Scene.TEXS_keys
    for cls in reversed(key_classes):
        bpy.utils.unregister_class(cls)


