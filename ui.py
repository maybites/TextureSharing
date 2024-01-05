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

        layout.operator("textureshare.directoryupdate", icon='WORLD_DATA', text='Update Directory')

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

            if item.texs_server != "OFF":
                sub1.prop(item, "enable", text = "", 
                        icon='CHECKBOX_HLT' if item.enable else 'CHECKBOX_DEHLT', 
                        emboss = False)
            
                sub1.label(icon='IMPORT')

                        
            sub2 = row.row()
            sub2.active = item.enable
            sub2.label(text=item.name)

            subsub = sub2.row(align=True)
            subsub.operator("textureshare.createitem", icon='ADD', text='').copy = index
            subsub.operator("textureshare.deleteitem", icon='PANEL_CLOSE', text = "").index = index

            if item.ui_expanded:
                dataColumn = colsub.column(align=True)
                dataSplit = dataColumn.split(factor = 0.2)
                
                colLabel = dataSplit.column(align = True)
                colData = dataSplit.column(align = True)
                
                colLabel.label(text='Desc.')
                address_row = colData.row(align = True)
                address_row.prop(item, 'name',text='', icon_only = True)
                           
                colLabel.label(text='Server')
                datapath_row = colData.row(align = True)
                datapath_row.prop(item, 'texs_server',text='')

                colLabel.label(text='Image')
                image_row = colData.row(align = True)
                image_row.prop(item, 'texs_image',text='')

            index = index + 1

        layout.operator("textureshare.createitem", icon='PRESET_NEW', text='Create new texture receiver').copy = -1


classes = (
    TEXS_PT_camera_texshare,
    TEXS_PT_Receiving
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

