# Spout addon for Blender

Spout for Blender allows to stream [spout](http://spout.zeal.co/) streams from blender.

This works only for Windows 10 64 bit.

## Installation

my personal preference to install addons: create a folder called 'blender' inside documents (or any other for you suitable location) and create the following folder structure inside:

* scripts
    * addons
    * modules

[download](https://github.com/maybites/blender.script.spout/releases) the addon, unzip it and drop the 'spout' folder inside the addons-folder

[download](https://github.com/maybites/Spout-for-Python/blob/master/Library/SpoutSDK.pyd) the SpoutSDK-library and drop it inside the modules-folder.

(if somebody knows a better way to deal with the library, please let me know, but putting it next to the _init__ files doesn't work)

inside blender: Menu > Edit > Preferences > FilePaths > Data > Scripts >  select the 'scripts' folder you created above.

restart blender.

inside blender: Menu > Edit > Preferences > Add-addons

Select tab 'TESTING'. you should now see the plugin called 'Render: Spout'

Enable it, save preferences and close preferences.

## Usage

Currently it is only possible to send Spout streams, but not to receive them.

For streaming you need a Camera object.

The plugin adds a Panel to the Camera properties called 'Streamin Texture'. The following properties are available:

* The streaming name is fixed to the camera name.
* capture/streaming resolution.

You should be able to create as many Cameras with streams as you wish.

The render settings are currently taken from the main 3d View settings.

## Issues

* Some Nvdia GFX-cards have a problem when in EEVEE the render method is set to 'LookDev' and 'Rendered'. There is bug report open where you can add your hardware specs if you encounter this issue.


## Syphon

No, this is addon is unable to stream syhon on OSX. But I had a chat with the syphon developers and it is feasible to make it happen, too. The only thing that is needed is a Objective-C -> Python wrapper. But unfortunately this is beyond my development abilities. If you think you have the necessary skills, please contact me. I would like to see Syphon for Blender happening, too.

## Credits

Without the [Spout for Python library](https://github.com/maybites/Spout-for-Python) developed by Ryan Walker and the valuable [hint](https://docs.blender.org/api/blender2.8/gpu.html#rendering-the-3d-view-into-a-texture) from Jonas Dichelle I would still dab into darckness...
