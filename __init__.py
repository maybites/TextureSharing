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
    "blender" : (2, 80, 0),
    "version" : (1, 0),
    "location" : "Properties > Camera > Camera data",
    "warning" : "This plugin works only if the SpoutSDK.pyd is inside '~/scripts/modules'",
    "category" : "Render", 
    "wiki_url" : "https://github.com/maybites/blender.script.spout",
    "tracker_url" : "https://github.com/maybites/blender.script.spout/issues",
    "support" : "TESTING"
}

import bpy
from bpy.types import Panel

import SpoutSDK
import bgl
import gpu
import uuid
from gpu_extras.presets import draw_texture_2d

#dictionary to store the references to
db_drawHandle = {} # the draw handler 
db_spoutInstances = {} # the spout instance

# function for the draw handler to capture the texture from the perspective of the camera
def texshare_capture(self, context, camera, object, offscreen, spoutSender):
    scene = context.scene
    dWIDTH = camera.texshare.capture_width
    dHEIGHT = camera.texshare.capture_height
     
    view_matrix = object.matrix_world.inverted()

    projection_matrix = object.calc_matrix_camera(
        context.depsgraph, x=dWIDTH, y=dHEIGHT)

    offscreen.draw_view3d(
        scene,
        context.view_layer,
        context.space_data,
        context.region,
        view_matrix,
        projection_matrix)

    bgl.glDisable(bgl.GL_DEPTH_TEST)
    draw_texture_2d(offscreen.color_texture, (10, 10), 40, 40)
       
    spoutSender.SendTexture(offscreen.color_texture, bgl.GL_TEXTURE_2D, dWIDTH, dHEIGHT, True, 0)
   
# main function called when the settings 'enable' property is changed
def texshare_main(self, context):
    global db_drawHandle
    global db_spoutInstances
    
    # my database ID
    dbID = context.camera.texshare.dbID
    
    # if streaming has been enabled and no id has yet been stored in the db
    if context.camera.texshare.enable == 1 and dbID not in db_drawHandle:
        # first we create a unique identifier for the reference db dicts
        dbID = str(uuid.uuid1())
        
        dWIDTH = context.camera.texshare.capture_width
        dHEIGHT = context.camera.texshare.capture_height
        
        # create a new spout sender instance
        spoutSender = SpoutSDK.SpoutSender()
        spoutSender.CreateSender(context.camera.name, dWIDTH, dHEIGHT, 0)        
        
        # create a off screen renderer
        offscreen = gpu.types.GPUOffScreen(dWIDTH, dHEIGHT)
        
        # collect all the arguments to pass to the draw handler
        args = (self, context, context.camera, context.object, offscreen, spoutSender)
        
        # instantiate the draw handler, 
        # using the texshare_capture function defined above
        drawhandle = bpy.types.SpaceView3D.draw_handler_add(texshare_capture, args, 'WINDOW', 'POST_PIXEL')
        
        # store the references inside the db-dicts
        db_drawHandle[dbID] = drawhandle
        db_spoutInstances[dbID] = spoutSender
        
    # if streaming has been disabled and my ID is still stored in the db
    if context.camera.texshare.enable == 0 and dbID in db_drawHandle:
        bpy.types.SpaceView3D.draw_handler_remove(db_drawHandle[dbID], 'WINDOW')
        db_spoutInstances[dbID].ReleaseSender(0)
        #removing my ID
        db_drawHandle.pop(dbID, None)
        dbID == "off"
    
    # store the database ID again inside the settings
    context.camera.texshare.dbID = dbID

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
    capture_width : bpy.props.IntProperty(
        name = "capture width",
        default = 1280,
        description = "Capture resolution width in pixels"
    )
    capture_height : bpy.props.IntProperty(
        name = "capture hight",
        default = 720,
        description = "Capture resolution height in pixels"
    )
    dbID : bpy.props.StringProperty(
        name ="database ID",
        default= "off",
        description = "referenceID for database")


    
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
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw_header(self, context):
        cam = context.camera
        self.layout.prop(cam.texshare, "enable", text="", )
        
    def draw(self, context):
        layout = self.layout
        ob = context.object
        camera = context.camera

        layout.use_property_split = True

        layout.active = camera.texshare.enable

        row = layout.row(align=True)
        row.prop(ob.data, "name", text="server name")

        col = layout.column()

        sub = col.column(align=True)
        sub.prop(camera.texshare, "capture_width", slider=True)
        sub.prop(camera.texshare, "capture_height", slider=True)
        

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