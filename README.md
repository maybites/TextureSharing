# Spout addon V1.3 for Blender 3.0.0

Spout for Blender allows to stream [spout](http://spout.zeal.co/) streams from blender.

This works only for Windows 10 64 bit.

## Installation

Please make sure you have the most current Blender 3.0.0 installed.

my personal preference to install addons:

1. create a folder called 'blender' inside documents (or any other name at a suitable location) and create the following folder structure inside:

  * scripts
    * addons
    * modules

2. [download](https://github.com/maybites/blender.script.spout/releases) the addon, unzip it and drop the 'spout' folder inside the addons-folder

3. [download](https://github.com/maybites/blender.script.spout/releases/tag/Python_3.9) the Python SpoutSDK-library and drop it inside the modules-folder.

4. Make sure the current python version is installed and added to the Path environment variable. (Checkbox during the installation)

(if somebody knows a better way to deal with the library, please let me know, but putting it next to the _init__ files doesn't work)

inside blender:

4. Menu > Edit > Preferences > FilePaths > Data > Scripts >  select the 'scripts' folder you created above.

5. restart blender.

6. Menu > Edit > Preferences > Add-addons

7. Select tab 'TESTING'. you should now see the plugin called 'Render: Spout'

8. Enable it, save preferences and close preferences.

## Usage

Currently it is only possible to send Spout streams, but not to receive them.

For streaming you need a Camera object.

The plugin adds a Panel to the Camera properties called 'Streaming Texture'. The following properties are available:

* The streaming name is fixed to the camera name.
* capture/streaming resolution.

You should be able to create as many Cameras with streams as you wish.

The render settings are currently taken from the main 3d View settings.

## Syphon

No, this addon is unable to stream [syphon](http://syphon.v002.info/) on OSX. But I had a chat with the syphon developers and it is feasible to make it happen, too. The only thing that is needed is an Objective-C -> Python wrapper, which is doable. But unfortunately this is beyond my development abilities. If you think you have the necessary skills, please contact me. I would like to see Syphon for Blender happening, too.

## Credits

Blender Plugin by Martin Froehlich.

### Special Thanks:
Obviously Lyn Jarvis for developing Spout in the first place. And without the [Spout for Python library](https://github.com/maybites/Spout-for-Python) developed by Ryan Walker and the valuable [hint](https://docs.blender.org/api/master/gpu.html#rendering-the-3d-view-into-a-texture) from Jonas Dichelle I would still dab in darkness...
