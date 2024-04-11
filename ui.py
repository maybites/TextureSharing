import bpy
from bpy.types import Panel
from sys import platform
import textwrap
from . import operators

# helper method to render long texts in multiple lines inside a GUI panel
def _label_multiline(context, text, parent):
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)

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
        camera = context.camera
        settings = camera.TEXS_share
        self.layout.prop(settings, "enable", text="", )
        
    def draw(self, context):
        layout = self.layout
        ob = context.object
        camera = context.camera
        settings = camera.TEXS_share

        layout.use_property_split = True

        layout.active = 1 - settings.enable

        row = layout.row(align=True)
        row.prop(settings, "streamingType", text="Streaming Type")

        row = layout.row(align=True)
        row.prop(ob.data, "name", text="Sender name")
        
        row = layout.row(align=True)
        row.prop(settings, "applyColorManagmentSettings", text="Apply color managment")

        row = layout.row(align=True)
        row.prop(settings, "isflipped", text="Flip outgoing texture")

        row = layout.row(align=True)
        row.prop(settings, "preview", text="Show Preview")

        col = layout.column()

        sub = col.column(align=True)
        sub.prop(settings, "capture_width", slider=True)
        sub.prop(settings, "capture_height", slider=True)

        row = layout.row(align=True)
        row.prop_search(settings,'workspace',bpy.data,'workspaces',text='Shading')

        col = layout.column()

        sub = col.column(align=True)
        sub.prop_search(settings,'scene',bpy.data,'scenes',text='Scene')
        sub.prop_search(settings,'layer',bpy.data.scenes[settings.scene],'view_layers',text='Layer')

            
#######################################
#  TEXSHARE RX PANEL                  #
#######################################

class TEXS_PT_Receiving(bpy.types.Panel):
    bl_category = "Share Texture"
    bl_label = "Receive Textures"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        texture_type = context.scene.TEXS_streaming_type
        
        col = layout.column()
        index = 0
        for item in bpy.context.scene.TEXS_imgs:
            col_box = col.column()
            box = col_box.box()
            #box.enabled = not envars.isServerRunning
            colsub = box.column()
            row = colsub.row(align=True)

            row.prop(item, "ui_expanded", text = "", 
                        icon='DISCLOSURE_TRI_DOWN' if item.ui_expanded else 'DISCLOSURE_TRI_RIGHT', 
                        emboss = False)

            sub1 = row.row()

            if item.texs_server != "OFF" and item.texs_image != None:
                sub1.prop(item, "enable", text = "", 
                        icon='CHECKBOX_HLT' if item.enable else 'CHECKBOX_DEHLT', 
                        emboss = False)
            
                sub1.label(icon='IMPORT')

                        
            sub2 = row.row()
            sub2.label(text=item.texs_server)

            if not item.enable:
                subsub = sub2.row(align=True)
                subsub.operator("textureshare.deleteitem", icon='PANEL_CLOSE', text = "").index = index

            if item.ui_expanded:
                colsub.active = not item.enable
                dataColumn = colsub.column(align=True)
                dataSplit = dataColumn.split(factor = 0.2)
                
                colLabel = dataSplit.column(align = True)
                colData = dataSplit.column(align = True)
                           
                colLabel.label(text='Server')
                datapath_row = colData.row(align = True)
                datapath_row.prop(item, 'texs_server',text='')

                colLabel.label(text='Image')
                image_row = colData.row(align = True)
                image_row.prop(item, 'texs_image',text='')

                colLabel.label(text='Type')
                image_row = colData.row(align = True)
                image_row.prop(item, 'streaming_type', text='')
                image_row.active = 0

            index = index + 1

        generate = layout.column()
        dataSplit = generate.split(factor = 0.7)

        gen_server = dataSplit.column(align = True)
        gen_server.prop(context.scene, "TEXS_servers", text='')

        gen_refresh = dataSplit.column(align = True)
        gen_refresh.operator("textureshare.directoryupdate", text='Update')

        gen_type = generate.column(align=True)
        gen_type.prop(texture_type, 'streaming_type', text='Type')

        gen_create = generate.row(align = True)
        gen_create.operator("textureshare.createitem", icon='PRESET_NEW', text='Create new texture receiver').type = texture_type.streaming_type


classes = (
    TEXS_PT_camera_texshare,
    TEXS_PT_Receiving
)

def register():
    bpy.utils.register_class(TEXS_PT_camera_texshare)
    bpy.utils.register_class(TEXS_PT_Receiving)
    #if platform.startswith("darwin"):
    #    bpy.utils.register_class(TEXS_PT_Receiving)


def unregister():
    bpy.utils.unregister_class(TEXS_PT_camera_texshare)
    bpy.utils.unregister_class(TEXS_PT_Receiving)
    #if platform.startswith("darwin"):
    #    bpy.utils.unregister_class(TEXS_PT_Receiving)

