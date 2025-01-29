
bl_info = {
    "name": "Object cloning helper", 
    "blender": (3, 6, 0), 
    "category": "3D View", 
}

import bpy
import bmesh
import mathutils

import sys
import os

dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append( dir )
    
from utils_packages_install import *
need_packages = need_packages_installed()

if not need_packages:
    from panel_properties import *
    from panel_operators  import *
    from panel_draw       import *

    from utils_photogrammetry import *
    from panel_operators_photogrammetry import *
    from materials_operators import *


class MESH_PT_MeshEditPanel(bpy.types.Panel):
    bl_label = "Elastic mesh"
    bl_idname = "VIEW3D_PT_mesh_edit_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Elastic mesh"

    def draw(self, context):
        layout = self.layout

        mesh = get_selected_mesh()
        if mesh is None:
            layout.label( text="Select a mesh" )
            return
        editable = get_mesh_editable( mesh )
        if editable:
            layout.label( text="Drag vertices around in edit mode." )
            layout.label( text="Or make it not editable" )
            layout.operator("mesh.clear_mesh_editable", text="Make not editable")

            mesh_prop = mesh.data.mesh_prop

            #layout.label( text="Step 1" )
            layout.label( text="Algorithm" )
            layout.prop(mesh_prop, 'step_1', text='Algorithm')

            layout.prop( mesh.data.mesh_prop, 'apply_rigid_transform', text="Rigid Transform" )

            layout.prop( mesh.data.mesh_prop, 'decay_radius', text="Effective dist" )

            if mesh_prop.step_1 == 'inverse_dist':
                layout.prop( mesh.data.mesh_prop, 'id_power' )
                layout.prop( mesh.data.mesh_prop, 'id_epsilon' )
            elif mesh_prop.step_1 == 'gaussian_proc':
                layout.prop( mesh.data.mesh_prop, 'gp_regularization' )

            #layout.label( text="Step 2" )
            #layout.prop(mesh_prop, 'step_2', expand=True)

            #if mesh_prop.step_2 != 'none':
            #    layout.label( text="Step 3" )
            #    layout.prop(mesh_prop, 'step_3', expand=True)
                

            index = get_selected_anchor_index()
            if index >= 0:
                anchor = mesh.data.mesh_prop.anchors[index]
                layout.label( text=f"Pin #{index}" )
                layout.prop( anchor, 'metric', expand=True )
                layout.prop( anchor, 'radius', expand=True )
            
                layout.operator( "mesh.apply_radius",  text="Radius -> all selected" )
                layout.operator( "mesh.apply_metric",  text="Metric -> all selected" )

            layout.operator( "mesh.apply_transform",  text="Apply transform" )
            layout.operator( "mesh.revert_transform", text="Show original shape" )
            layout.operator( "mesh.add_anchors",      text="Make selected pins" )
            layout.operator( "mesh.remove_anchors",   text="Clear selected pins" )

        else:
            layout.operator("mesh.set_mesh_editable", text="Make editable")



# Panel for setting paths
class MESH_PT_ToolPathsPanel(bpy.types.Panel):
    bl_label = "Photogrammetry"
    bl_idname = "MESH_PT_tool_paths"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = 'scene'
    bl_category = 'Photogrammetry'
    
    def draw(self, context):
        layout = self.layout
        tool_paths = context.scene.tool_paths

        layout.label(text="FFMPEG path")
        layout.prop(tool_paths, "ffmpeg_path")

        layout.prop(tool_paths, "ffmpeg_frames")
        layout.prop(tool_paths, "ffmpeg_seconds")
        layout.prop(tool_paths, "ffmpeg_start_time", text="Start time")
        layout.prop(tool_paths, "ffmpeg_end_time", text="End time")

        layout.operator( "wm.call_ffmpeg", text="Extract frames" )


        props = context.scene.photogrammetry_properties

        layout.prop(tool_paths, "colmap_path")

        layout.operator( "wm.call_colmap", text="Extract camera poses" )
        
        layout.prop( props, 'additional_displacement', expand=True )
        layout.prop( props, 'additional_rotation', expand=True )
        layout.prop( props, 'additional_scale', expand=True )
        layout.operator( "wm.create_ref_images", text="Create Ref Images" )

        layout.label(text="Ref images")
        layout.prop( props, 'show_point_cloud', expand=True )
        #layout.prop( props, 'index', expand=True )
        layout.prop( context.scene.photogrammetry_properties, "camera_images_items", text="Ref. Image" )
        layout.operator( "wm.place_camera", text="Place camera" )


        layout.label(text="Texture paint stencil")
        layout.prop( props, 'stencil_scale_adj', expand=True )
        layout.operator( "wm.align_stencil", text="Align stencil" )






class MESH_PT_MeshInstallPackages(bpy.types.Panel):
    bl_label = "Install packages"
    bl_idname = "VIEW3D_PT_mesh_install_packages"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Install Packages"

    def draw(self, context):
        layout = self.layout

        layout.label( text="The plugin needs numpy and scipy!" )
        layout.label( text="Press the button to install and restart Blender." )
        layout.label( text="On Windows sometimes it complains about access rights." )
        layout.label( text="If it does and fails, just repeat it again!" )
        layout.operator("wm.mesh_install_packages", text="Install")









def register():
    global need_packages
    if need_packages:
        register_install_packages()
        bpy.utils.register_class(MESH_PT_MeshInstallPackages)
    else:
        register_properties()
        register_operators()
        register_photogrammetry_props()
        register_photogrammetry()
        bpy.utils.register_class(MESH_PT_MeshEditPanel)
        bpy.utils.register_class(MESH_PT_ToolPathsPanel)
        materials_register()

        register_draw()


def unregister():
    global need_packages
    if need_packages:
        bpy.utils.unregister_class(MESH_PT_MeshInstallPackages)
        unregister_install_packages()
    else:
        bpy.utils.unregister_class(MESH_PT_MeshEditPanel)
        bpy.utils.unregister_class(MESH_PT_ToolPathsPanel)
        materials_unregister()
        unregister_draw()
        unregister_operators()
        unregister_properties()
        unregister_photogrammetry()
        unregister_photogrammetry_props()

    
    


if __name__ == "__main__":
    register()


