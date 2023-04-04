import bpy
import bgl
import gpu
from gpu_extras.presets import draw_texture_2d

import json
from dataclasses import dataclass


try:
    from .fbs.FrameBufferSharingServer import FrameBufferSharingServer
except ModuleNotFoundError as ex:
    print(f"Could not load FrameSharingModule: {ex}")

import uuid

#dictionary to store the references to
db_frameHandle = {} # the draw handler 
db_drawHandle = {} # the draw handler 
db_spoutInstances = {} # the spout instance


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


# function for the draw handler to capture the texture from the perspective of the camera
def texshare_capture(self, context, camera, object, space, region, scene, layer, offscreen, spyphonSender, showPreview, frame_metadata_buffer):
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

    buffer =  frame_metadata_buffer.content

    #if spyphonSender.can_memory_buffer() == True:
    #    spyphonSender.write_memory_buffer(camera.name, buffer, len(buffer))

    spyphonSender.send_texture(offscreen.color_texture, dWIDTH, dHEIGHT, True)

          
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
        updateDraw = False
        
        dWIDTH = guivars.capture_width
        dHEIGHT = guivars.capture_height
        
        # create a new spout sender instance
        spyphonSender = FrameBufferSharingServer.create(context.camera.name)
        spyphonSender.setup()

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
        args = (self, context, context.camera, context.object, mySpace, myRegion, myScene, myLayer, offscreen, spyphonSender, guivars.preview, frame_metadata_buffer)
        
        frameHandler = frame_metadata(context.camera.name, frame_metadata_buffer)
        bpy.app.handlers.depsgraph_update_post.append(frameHandler)

        # instantiate the draw handler, 
        # using the texshare_capture function defined above
        drawhandle = bpy.types.SpaceView3D.draw_handler_add(texshare_capture, args, 'WINDOW', 'POST_PIXEL')
        
        # store the references inside the db-dicts
        db_frameHandle[dbID] = frameHandler
        db_drawHandle[dbID] = drawhandle
        db_spoutInstances[dbID] = spyphonSender
        
    # if streaming has been disabled and my ID is still stored in the db
    if context.camera.texshare.enable == 0 and dbID in db_drawHandle:
        bpy.app.handlers.depsgraph_update_post.remove(db_frameHandle[dbID])
        bpy.types.SpaceView3D.draw_handler_remove(db_drawHandle[dbID], 'WINDOW')
        db_spoutInstances[dbID].release()
        #removing my ID
        db_drawHandle.pop(dbID, None)
        dbID == "off"
    
    # store the database ID again inside the settings
    context.camera.texshare.dbID = dbID


def register():
    from bpy.utils import register_class
    # nothing

def unregister():
    from bpy.utils import unregister_class
    # nothing
