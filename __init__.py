
bl_info = {
    "name": "Cloning helper", 
    "blender": (4, 3, 2), 
    "category": "3D View", 
}

from . import panel_main


def register():
    panel_main.register()



def unregister():
    panel_main.unregister()



