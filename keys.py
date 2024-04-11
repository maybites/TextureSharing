import bpy
from . import operators

streamingTypeItems = set()

def add_streaming_type_ndi(items):
    items.add(("NDI", "NDI", "Use NDI for streaming", "NONE", 1))

def add_streaming_type_spout(items):
    items.add(("SPOUT", "Spout / Syphon", "Use Spout (for Windows) or Syphon (for OSX) for streaming", "NONE", 0))

# Read-only string property
def get_server_name(self):
    data = bpy.context.scene.TEXS_servers
    return data

class TEXS_PG_image_texshare_streaming_type(bpy.types.PropertyGroup):
    # Define a StringProperty for the filepath
    streaming_type: bpy.props.EnumProperty(
        name = "stream type", 
        default = "SPOUT", 
        items = streamingTypeItems
    )

class TEXS_PG_image_texshare_settings(bpy.types.PropertyGroup):
    #key_path = bpy.props.StringProperty(name="Key", default="Unknown")
    enable: bpy.props.BoolProperty(
        name="Enable", 
        description = "Enables texture sharing", 
        default=False,
        update=operators.texshare_receive
    )
    has_started : bpy.props.BoolProperty(
        name = "hasstarted",
        default = 0,
        description = "Inidicates if sharing has been activated"
    )
    is_running : bpy.props.BoolProperty(
        name = "isrunning",
        default = 0,
        description = "Inidicates if sharing is active"
    )
    is_flipped : bpy.props.BoolProperty(
        name = "isflipped",
        default = 0,
        description = "Inidicates if the texture is flipped when sharing is active"
    )   
    name: bpy.props.StringProperty(
        name="Name", 
        default="TextureReceiver"
    )
    texs_server: bpy.props.StringProperty(
        name = "Server", 
        get=get_server_name
    )
    texs_image: bpy.props.PointerProperty(
        name="Image", 
        type=bpy.types.Image
    )
    ui_expanded: bpy.props.BoolProperty(
        name="Expanded", 
        default=True
    )
    dbID : bpy.props.StringProperty(
        name ="database ID",
        default= "off",
        description = "referenceID for database"
    )
    streaming_type: bpy.props.StringProperty(
        name = "streaming_type", 
        default = "SPOUT", 
        description = "streaming type"
    )


class TEXS_PG_camera_texshare_settings(bpy.types.PropertyGroup):
    streamingType: bpy.props.EnumProperty(
        name = "streaming type", 
        default = "SPOUT", 
        items = streamingTypeItems
    )
    enable : bpy.props.BoolProperty(
        name = "enable",
        default = 0,
        description = "Enables texture sharing", 
        update=operators.texshare_send
    )
    hasstarted : bpy.props.BoolProperty(
        name = "hasstarted",
        default = 0,
        description = "Inidicates if sharing has been activated"
    )
    isrunning : bpy.props.BoolProperty(
        name = "isrunning",
        default = 0,
        description = "Inidicates if sharing is active"
    )
    isflipped : bpy.props.BoolProperty(
        name = "isflipped",
        default = 0,
        description = "Inidicates if the texture is flipped when sharing is active"
    )
    applyColorManagmentSettings : bpy.props.BoolProperty(
        name = "applyColorManagmentSettings",
        default = 1,
        description = "Applies the current scene color management settings"
    )
    capture_width : bpy.props.IntProperty(
        name = "Capture width",
        default = 1280,
        description = "Capture resolution width in pixels"
    )
    capture_height : bpy.props.IntProperty(
        name = "Capture hight",
        default = 720,
        description = "Capture resolution height in pixels"
    )
    dbID : bpy.props.StringProperty(
        name ="database ID",
        default= "off",
        description = "referenceID for database"
    )
    workspace : bpy.props.StringProperty(
        name ="workspace",
        default= "Layout",
        description = "Workspace from which to use the Overlay and Shading properties"
    )
    scene : bpy.props.StringProperty(
        name ="scene",
        default= "Scene",
        description = "Scene to render"
    )
    layer : bpy.props.StringProperty(
        name ="layer",
        default= "ViewLayer",
        description = "Layer in Scene to render"
    )
    preview : bpy.props.BoolProperty(
        name ="Preview",
        default= 0,
        description = "Show preview of shared texture inside viewport"
    )


key_classes = (
    TEXS_PG_image_texshare_settings,
    TEXS_PG_camera_texshare_settings,
    TEXS_PG_image_texshare_streaming_type
)

def register():
    for cls in key_classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.TEXS_streaming_type = bpy.props.PointerProperty(type=TEXS_PG_image_texshare_streaming_type)
    bpy.types.Scene.TEXS_imgs = bpy.props.CollectionProperty(type=TEXS_PG_image_texshare_settings)
    bpy.types.Camera.TEXS_share = bpy.props.PointerProperty(type=TEXS_PG_camera_texshare_settings)
    

def unregister():
    for cls in reversed(key_classes):
        bpy.utils.unregister_class(cls) 
    
    del bpy.types.Scene.TEXS_imgs
    del bpy.types.Scene.TEXS_streaming_type
    del bpy.types.Camera.TEXS_share
    

