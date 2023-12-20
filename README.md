# Spout and Syphon addon V4.0.0 for Blender 3.0.x

Blender addon that allows to stream [spout](http://spout.zeal.co/) and [Syphon](https://syphon.github.io/) streams from blender.

This works for current Windows and OSX.

## Installation

Please make sure you have the most current Blender 3.0.x installed.

1. IMPORTANT: [download](https://github.com/maybites/blender.script.spout/releases) the addon from the **releases**

2. Open Blender > Menu >  Preferences > Add-ons > search for and enable the 'Spout' add-on  

3. Press the button to install the SpoutGL or syphon library via pip.

4. Once the library is installed, disable and reenable the addon.

5. Save and close preferences.

## Usage

Currently it is only possible to send Spout and Syphon streams, but not to receive them.

For streaming you need a Camera object.

The plugin adds a Panel to the Camera properties called 'Streaming Texture'. The following properties are available:

* The streaming name is default set to the camera name.
* capture/streaming resolution.
* show preview inside viewport.
* vertical flip of the sent texture.
* use eevee color management (recommended)
* chose a workspace with the desired render / shading preferences
* chose a scene and layer setup to render

You should be able to create as many Cameras with streams as you wish.

## Credits

Blender Plugin by Martin Froehlich.

### Special Thanks:

* Lyn Jarvis for developing [Spout](http://spout.zeal.co/)
* Tom Butterworth and Anton Marini  for developing [Syphon](https://syphon.github.io/)
* Jason for the python wrappper [SpoutGL for Python](https://github.com/jlai/Python-SpoutGL) 
* Florian Bruggisser for the python wrappper [syphon-python](https://github.com/cansik/syphon-python)
* The valuable [hint](https://docs.blender.org/api/master/gpu.html#rendering-the-3d-view-into-a-texture) from Jonas Dichelle I would still dab in darkness...
* [CAD_Sketcher](https://github.com/hlorus/CAD_Sketcher) showed me how to dynamically install the needed libraries. Hurray to Opensource!

### Very Special Thanks

Python support by Florian Bruggisser - without him, the flawless working of spyhon in blender would still be a dream.
