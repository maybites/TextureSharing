import bpy
from bpy.types import Panel
import textwrap
from . import operators

# helper method to render long texts in multiple lines inside a GUI panel
def _label_multiline(context, text, parent):
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)


class TEXS_PG_camera_texshare_settings(bpy.types.PropertyGroup):
    enable : bpy.props.BoolProperty(
        name = "enable",
        default = 0,
        description = "enables the texture streaming", 
        update=operators.texshare_main
    )
    hasstarted : bpy.props.BoolProperty(
        name = "hasstarted",
        default = 0,
        description = "inidicates if streaming has been activated"
    )
    isrunning : bpy.props.BoolProperty(
        name = "isrunning",
        default = 0,
        description = "inidicates if streaming is active"
    )
    applyColorManagmentSettings : bpy.props.BoolProperty(
        name = "applyColorManagmentSettings",
        default = 1,
        description = "applies the current scenes color management settings"
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
        description = "Show preview of streamed texture inside viewport"
        )

class CameraButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        engine = context.engine
        return context.camera and (engine in cls.COMPAT_ENGINES)

class TEXS_PT_camera_texshare( CameraButtonsPanel, Panel ):
    bl_label = "Streaming Texture"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES'}

    def draw_header(self, context):
        cam = context.camera
        self.layout.prop(cam.texshare, "enable", text="", )
        
    def draw(self, context):
        layout = self.layout
        ob = context.object
        camera = context.camera

        layout.use_property_split = True

        layout.active = 1 - camera.texshare.enable

        row = layout.row(align=True)
        row.prop(ob.data, "name", text="Server name")
        
        row = layout.row(align=True)
        row.prop(camera.texshare, "applyColorManagmentSettings", text="Apply color managment")

        row = layout.row(align=True)
        row.prop(camera.texshare, "preview", text="Show Preview")

        col = layout.column()

        sub = col.column(align=True)
        sub.prop(camera.texshare, "capture_width", slider=True)
        sub.prop(camera.texshare, "capture_height", slider=True)

        row = layout.row(align=True)
        row.prop_search(camera.texshare,'workspace',bpy.data,'workspaces',text='Shading')

        col = layout.column()

        sub = col.column(align=True)
        sub.prop_search(camera.texshare,'scene',bpy.data,'scenes',text='Scene')
        sub.prop_search(camera.texshare,'layer',bpy.data.scenes[camera.texshare.scene],'view_layers',text='Layer')

classes = (
    TEXS_PG_camera_texshare_settings,
    TEXS_PT_camera_texshare
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Camera.texshare = bpy.props.PointerProperty(type=TEXS_PG_camera_texshare_settings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Camera.texshare
