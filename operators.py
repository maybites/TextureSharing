import bpy
import gpu
import time
from gpu_extras.presets import draw_texture_2d

import json
from dataclasses import dataclass

try:
    from .fbs.FrameBufferSharingServer import FrameBufferSharingServer
    from .fbs.FrameBufferSharingClient import FrameBufferSharingClient
    from .fbs.FrameBufferDirectory import FrameBufferDirectory
except ModuleNotFoundError as ex:
    print(f"Could not load FrameSharingModule: {ex}")

import uuid

fb_directory = FrameBufferDirectory.create("FrameBufferDirectory")
fb_directory.setup()

#dictionary to store the references to
db_frameHandle = {} # the draw handler 
db_drawHandle = {} # the draw handler 
db_cameraInstances = {} # the server instance

db_writeHandle = {} # the write handler 
db_clientInstances = {} # the client instance

@dataclass
class FrameMetDataBuffer:
    content: str = ""

def frame_metadata(name, frame_metadata_buffer):
    def handler(scene, depsgraph):
        camera = scene.objects.get(name)
        if not camera:
            return

        container = {}
        container['version'] = 1 
        container['frame'] = scene.frame_current
        container['ts'] = 0

        extrinsic = {}
        extrinsic['pos'] = [camera.location[0], camera.location[1], camera.location[2]]
        extrinsic['quat'] = [camera.rotation_quaternion[0], camera.rotation_quaternion[1], camera.rotation_quaternion[2], camera.rotation_quaternion[3]]
        extrinsic['matrix'] = [camera.matrix_world[0][0], camera.matrix_world[0][1], camera.matrix_world[0][2], camera.matrix_world[0][3], camera.matrix_world[1][0], camera.matrix_world[1][1], camera.matrix_world[1][2], camera.matrix_world[1][3], camera.matrix_world[2][0], camera.matrix_world[2][1], camera.matrix_world[2][2], camera.matrix_world[2][3], camera.matrix_world[3][0], camera.matrix_world[3][1], camera.matrix_world[3][2], camera.matrix_world[3][3]]

        container['extrinsic'] = extrinsic

        fraMeDaPro = {}
        fraMeDaPro['freMeDaPro'] = container
        frame_metadata_buffer.content = json.dumps(fraMeDaPro)
    return handler

def write_frame(fb_client, guivars):
    def write_frame_handler(scene, depsgraph):
        if fb_client.has_new_frame() == True:
            fb_client.apply_frame_to_image(guivars.texs_image)
    
    return write_frame_handler

# function for the draw handler to capture the texture from the perspective of the camera
def texshare_capture(self, context, camera, object, space, region, scene, layer, offscreen, spyphonSender, showPreview, isFlipped, frame_metadata_buffer):
    guivars = camera.TEXS_share

    dWIDTH = guivars.capture_width
    dHEIGHT = guivars.capture_height
    applyCM = guivars.applyColorManagmentSettings

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
        gpu.state.depth_test_set("NONE")
        spyphonSender.draw_texture(offscreen, (10, 10), dWIDTH / 4, dHEIGHT / 4)

    #if spyphonSender.can_memory_buffer() == True:
    #    spyphonSender.write_memory_buffer(camera.name, buffer, len(buffer))

    spyphonSender.send_texture(offscreen, dWIDTH, dHEIGHT, isFlipped)

          
# main function called when the settings 'enable' property is changed
def texshare_send(self, context):
    global db_drawHandle
    global db_cameraInstances
    
    guivars = context.camera.TEXS_share
    
    # my database ID
    dbID = guivars.dbID
    
    # if streaming has been enabled and no id has yet been stored in the db
    if guivars.enable == 1 and dbID not in db_drawHandle:
        # first we create a unique identifier for the reference db dicts
        dbID = str(uuid.uuid1())
        updateDraw = False
        
        dWIDTH = guivars.capture_width
        dHEIGHT = guivars.capture_height
        
        # create a new spout sender instance
        fbSender = FrameBufferSharingServer.create(context.camera.name, guivars.streamingType)
        fbSender.setup()

        #if spyphonSender.can_memory_buffer() == True:
        ##    spyphonSender.create_memory_buffer(context.camera.name, 1024)

        # create a off screen renderer
        offscreen = gpu.types.GPUOffScreen(dWIDTH, dHEIGHT)

        mySpace = context.space_data
        myRegion = context.region
 
        for area in bpy.data.workspaces[guivars.workspace].screens[0].areas:
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

        frame_metadata_buffer = FrameMetDataBuffer("test")

        # collect all the arguments to pass to the draw handler
        args = (self, context, context.camera, context.object, mySpace, myRegion, myScene, myLayer, offscreen, fbSender, guivars.preview, guivars.isflipped, frame_metadata_buffer)
        
        # frameHandler = frame_metadata(context.camera.name, frame_metadata_buffer)
        # bpy.app.handlers.depsgraph_update_post.append(frameHandler)

        # instantiate the draw handler, 
        # using the texshare_capture function defined above
        drawhandle = bpy.types.SpaceView3D.draw_handler_add(texshare_capture, args, 'WINDOW', 'POST_PIXEL')
        
        # store the references inside the db-dicts
        #db_frameHandle[dbID] = frameHandler
        db_drawHandle[dbID] = drawhandle
        db_cameraInstances[dbID] = fbSender
        
    # if streaming has been disabled and my ID is still stored in the db
    if guivars.enable == 0 and dbID in db_drawHandle:
        #bpy.app.handlers.depsgraph_update_post.remove(db_frameHandle[dbID])
        bpy.types.SpaceView3D.draw_handler_remove(db_drawHandle[dbID], 'WINDOW')
        db_cameraInstances[dbID].release()
        #removing my ID
        db_drawHandle.pop(dbID, None)
        dbID == "off"
    
    # store the database ID again inside the settings
    guivars.dbID = dbID

          
# main function called when the share receive 'enable' property is changed
def texshare_receive(self, context):
    global db_writeHandle
    global db_clientInstances
    
    guivars = self
    
    # my database ID
    dbID = guivars.dbID
  
    # if streaming has been enabled and no id has yet been stored in the db
    if guivars.enable == 1 and dbID not in db_writeHandle:
        # first we create a unique identifier for the reference db dicts
        dbID = str(uuid.uuid1())
        updateDraw = False

        server = guivars.texs_server
        
        # create a new spout sender instance
        fb_client = FrameBufferSharingClient.create(server)
        fb_client.setup(fb_directory.get_server(server))

        # create a off screen renderer
        # offscreen = gpu.types.GPUOffScreen(dWIDTH, dHEIGHT)

        # collect all the arguments to pass to the write handler
        
        write_handler = None
        write_handler = write_frame(fb_client, guivars)
        bpy.app.handlers.depsgraph_update_pre.append(write_handler)
        
        # store the references inside the db-dicts
        #db_frameHandle[dbID] = frameHandler
        db_writeHandle[dbID] = write_handler
        db_clientInstances[dbID] = fb_client

    # if streaming has been disabled and my ID is still stored in the db
    if guivars.enable == 0 and dbID in db_writeHandle:
        bpy.app.handlers.depsgraph_update_pre.remove(db_writeHandle[dbID])
        db_clientInstances[dbID].release()
        #removing my ID
        db_writeHandle.pop(dbID, None)
        dbID == "off"
    
    # store the database ID again inside the settings
    guivars.dbID = dbID


class TEXS_OT_ItemCreate(bpy.types.Operator):
    """Create new texture receiver"""
    bl_idname = "textureshare.createitem"
    bl_label = "Create"

    type: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        keys = bpy.context.scene.TEXS_imgs
        new_item = keys.add()
        # we assume the new key is added at the end of the collection, so we get the index by:
        index = len(bpy.context.scene.TEXS_imgs.keys()) -1 
        new_item.streaming_type = self.type
        if self.type == 'SPOUT':
            new_item.name = "SpoutReceiver"
        if self.type == 'NDI':
            new_item.name = "NDIReceiver"

        return {'RUNNING_MODAL'}


#######################################
#  Delete TEXS Settings               #
#######################################

class TEXS_OT_ItemDelete(bpy.types.Operator):
    """Delete this texture receiver"""
    bl_idname = "textureshare.deleteitem"
    bl_label = "Delete"

    index: bpy.props.IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        bpy.context.scene.TEXS_imgs.remove(self.index)
        return {'RUNNING_MODAL'}

#######################################
#  UPDATE TEXS DIRECTORY              #
#######################################

class TEXS_OT_DirUpdate(bpy.types.Operator):
    """update frame share directory"""
    bl_idname = "textureshare.directoryupdate"
    bl_label = "Update"

    global fb_directory

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        fb_directory.update()
        return {'RUNNING_MODAL'}

op_classes = (
    TEXS_OT_ItemCreate,
    TEXS_OT_ItemDelete,
    TEXS_OT_DirUpdate,
)

def register():
    for cls in op_classes:
        bpy.utils.register_class(cls)

    fb_directory.register()

def unregister():
    for cls in reversed(op_classes):
        bpy.utils.unregister_class(cls)

    fb_directory.unregister()
