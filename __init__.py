# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Spout",
    "author" : "Martin Froehlich",
    "description" : "Streaming Spout from Blender",
    "blender" : (3, 0, 0),
    "version" : (2, 0, 1),
    "location" : "Properties > Camera > Camera data",
    "warning" : "This plugin works only if the SpoutGL (https://pypi.org/project/SpoutGL/#files) is inside '~/scripts/modules'",
    "category" : "Render", 
    "wiki_url" : "https://github.com/maybites/blender.script.spout",
    "tracker_url" : "https://github.com/maybites/blender.script.spout/issues",
    "support" : "COMMUNITY"
}

import bpy
from bpy.types import Panel

import SpoutGL
import bgl
import gpu
import uuid
import textwrap
from gpu_extras.presets import draw_texture_2d

#dictionary to store the references to
db_drawHandle = {} # the draw handler 
db_spoutInstances = {} # the spout instance

# function for the draw handler to capture the texture from the perspective of the camera
def texshare_capture(self, context, camera, object, space, region, scene, layer, offscreen, spoutSender, showPreview):
    dWIDTH = camera.texshare.capture_width
    dHEIGHT = camera.texshare.capture_height
    applyCM = camera.texshare.applyColorManagmentSettings

    view_matrix = object.matrix_world.inverted()

    projection_matrix = object.calc_matrix_camera(
        context.evaluated_depsgraph_get(), x=dWIDTH, y=dHEIGHT)

    #bpy.data.screens['3DView'].areas[0].regions[0]

    offscreen.draw_view3d(
        scene,
        layer,
        space,
        context.region,
        view_matrix,
        projection_matrix,
        do_color_management=applyCM)

    if showPreview:
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        draw_texture_2d(offscreen.color_texture, (10, 10), dWIDTH / 4, dHEIGHT / 4)

    spoutSender.sendTexture(offscreen.color_texture, bgl.GL_TEXTURE_2D, dWIDTH, dHEIGHT, True, 0)
    spoutSender.setFrameSync(camera.name)
 
         
# main function called when the settings 'enable' property is changed
def texshare_main(self, context):
    global db_drawHandle
    global db_spoutInstances
    
    guivars = context.camera.texshare
    
    # my database ID
    dbID = guivars.dbID
    
    # if streaming has been enabled and no id has yet been stored in the db
    if context.camera.texshare.enable == 1 and dbID not in db_drawHandle:
        # first we create a unique identifier for the reference db dicts
        dbID = str(uuid.uuid1())
        
        dWIDTH = guivars.capture_width
        dHEIGHT = guivars.capture_height
        
        # create a new spout sender instance
        spoutSender = SpoutGL.SpoutSender()
        spoutSender.setSenderName(context.camera.name)       
        
        # create a off screen renderer
        offscreen = gpu.types.GPUOffScreen(dWIDTH, dHEIGHT)

        mySpace = context.space_data
        myRegion = context.region
 
        for area in bpy.data.screens[guivars.workspace].areas:
            if area.type == 'VIEW_3D':
                myRegion = area.regions[0]
                for spaces in area.spaces:
                    if spaces.type == 'VIEW_3D':
                        mySpace = spaces

        myScene = bpy.data.scenes[guivars.scene]
        myLayer = myScene.view_layers[guivars.layer]

        myCurrentScene = bpy.context.window.scene
        myCurrentLayer = bpy.context.window.view_layer

        # quickly open the to be rendered scene and layer to avoid a crash of blender
        bpy.context.window.scene = myScene
        bpy.context.window.view_layer = myLayer

        bpy.context.window.scene = myCurrentScene
        bpy.context.window.view_layer = myCurrentLayer

        # collect all the arguments to pass to the draw handler
        args = (self, context, context.camera, context.object, mySpace, myRegion, myScene, myLayer, offscreen, spoutSender, guivars.preview)
        
        # instantiate the draw handler, 
        # using the texshare_capture function defined above
        drawhandle = bpy.types.SpaceView3D.draw_handler_add(texshare_capture, args, 'WINDOW', 'POST_PIXEL')
        
        # store the references inside the db-dicts
        db_drawHandle[dbID] = drawhandle
        db_spoutInstances[dbID] = spoutSender
        
    # if streaming has been disabled and my ID is still stored in the db
    if context.camera.texshare.enable == 0 and dbID in db_drawHandle:
        bpy.types.SpaceView3D.draw_handler_remove(db_drawHandle[dbID], 'WINDOW')
        db_spoutInstances[dbID].releaseSender()
        #removing my ID
        db_drawHandle.pop(dbID, None)
        dbID == "off"
    
    # store the database ID again inside the settings
    context.camera.texshare.dbID = dbID

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
        update=texshare_main
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
        default = 0,
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
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Camera.texshare = bpy.props.PointerProperty(type=TEXS_PG_camera_texshare_settings)

def unregister():
    del bpy.types.Camera.texshare
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
