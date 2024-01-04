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
        description = "Enables texture sharing", 
        update=operators.texshare_main
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

class CameraButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        engine = context.engine
        return context.camera and (engine in cls.COMPAT_ENGINES)

class TEXS_PT_camera_texshare( CameraButtonsPanel, Panel ):
    bl_label = "Share Texture"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES', 'BLENDER_EEVEE_NEXT'}

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
        row.prop(ob.data, "name", text="Sender name")
        
        row = layout.row(align=True)
        row.prop(camera.texshare, "applyColorManagmentSettings", text="Apply color managment")

        row = layout.row(align=True)
        row.prop(camera.texshare, "isflipped", text="Flip outgoing texture")

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

            
#######################################
#  TEXSHARE RX PANEL                  #
#######################################

class TEXS_PT_Receiving(bpy.types.Panel):
    bl_category = "Share Texture"
    bl_label = "Receive Textures"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        index = 0
        for item in bpy.context.scene.TEXS_keys:
            col_box = col.column()
            box = col_box.box()
            #box.enabled = not envars.isServerRunning
            colsub = box.column()
            row = colsub.row(align=True)

            row.prop(item, "ui_expanded", text = "", 
                        icon='DISCLOSURE_TRI_DOWN' if item.ui_expanded else 'DISCLOSURE_TRI_RIGHT', 
                        emboss = False)

            sub1 = row.row()
            sub1.prop(item, "enabled", text = "", 
                        icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT', 
                        emboss = False)
            
            sub1.label(icon='IMPORT')
                        
            sub2 = row.row()
            sub2.active = item.enabled
            sub2.label(text=item.description)

            subsub = sub2.row(align=True)
            subsub.operator("textureshare.createitem", icon='ADD', text='').copy = index
            subsub.operator("textureshare.deleteitem", icon='PANEL_CLOSE', text = "").index = index

            if item.ui_expanded:
                dataColumn = colsub.column(align=True)
                dataSplit = dataColumn.split(factor = 0.2)
                
                colLabel = dataSplit.column(align = True)
                colData = dataSplit.column(align = True)
                
                colLabel.label(text='description')
                address_row = colData.row(align = True)
                address_row.prop(item, 'description',text='', icon_only = True)
                           
                colLabel.label(text='source')
                datapath_row = colData.row(align = True)
                datapath_row.prop(item, 'texs_source',text='')
                                              
            index = index + 1

        layout.operator("textureshare.createitem", icon='PRESET_NEW', text='Create new texture receiver').copy = -1


classes = (
    TEXS_PG_camera_texshare_settings,
    TEXS_PT_camera_texshare,
    TEXS_PT_Receiving
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Camera.texshare = bpy.props.PointerProperty(type=TEXS_PG_camera_texshare_settings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Camera.texshare
