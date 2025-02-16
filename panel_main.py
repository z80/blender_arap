
import bpy
import bmesh
import mathutils

import sys
import os

#dir = os.path.dirname(bpy.data.filepath)
#if not dir in sys.path:
#    sys.path.append( dir )
    
from .utils_packages_install import *
need_packages = need_packages_installed()

if not need_packages:
    from .panel_properties import *
    from .panel_operators  import *
    from .panel_draw       import *

    from .utils_photogrammetry import *
    from .panel_operators_photogrammetry import *
    from .materials_operators import *


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

            box = layout.box()
            #layout.label( text="Step 1" )
            box.label( text="Algorithm" )
            box.prop(mesh_prop, 'step_1', text='Algorithm')

            box.prop( mesh.data.mesh_prop, 'apply_rigid_transform', text="Rigid Transform" )

            box.prop( mesh.data.mesh_prop, 'decay_radius', text="Effective dist" )

            if mesh_prop.step_1 == 'inverse_dist':
                box.prop( mesh.data.mesh_prop, 'id_power' )
                box.prop( mesh.data.mesh_prop, 'id_epsilon' )
            elif mesh_prop.step_1 == 'gaussian_proc':
                box.prop( mesh.data.mesh_prop, 'gp_regularization' )

            box = layout.box()
            box.label( text="Step 2" )
            box.prop(mesh_prop, 'step_2')
            if ( mesh_prop.step_2 != 'none' ):
                box.prop( mesh.data.mesh_prop, 'normal_importance' )
                box.prop( mesh.data.mesh_prop, 'num_iterations' )

            if mesh_prop.step_2 != 'none':
                box = layout.box()
                box.label( text="Step 3" )
                box.prop(mesh_prop, 'step_3')
            
            layout.separator()

            index = get_selected_anchor_index()
            if index >= 0:
                box = layout.box()
                anchor = mesh.data.mesh_prop.anchors[index]
                box.label( text=f"Pin #{index}" )
                box.prop( anchor, 'metric', expand=True )
                box.prop( anchor, 'radius', expand=True )
            
                box.operator( "mesh.apply_radius",  text="Radius -> all selected" )
                box.operator( "mesh.apply_metric",  text="Metric -> all selected" )
                box.operator( "mesh.reset_selected_pins", text="Reset Selected Positions" )

                layout.separator()
            
            row = layout.row()
            row.scale_y = 2.0
            layout.prop( mesh.data.mesh_prop, 'draw_pins', text="Draw Pins" )
            row.operator( "mesh.apply_transform",  text="Apply transform" )

            layout.separator()
            #layout.operator( "mesh.apply_transform",  text="Apply transform" )
            layout.operator( "mesh.revert_transform", text="Show original shape" )
            layout.operator( "mesh.add_anchors",      text="Make selected pins" )
            layout.operator( "mesh.remove_anchors",   text="Clear selected pins" )

            layout.separator()
            
            box = layout.box()
            row = box.row()
            row.operator( "file.save_pins",  text="Save Pins" )
            row.operator( "file.load_pins",  text="Load Pins" )



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

        box = layout.box()
        box.label(text="FFMPEG path")
        box.prop(tool_paths, "ffmpeg_path")

        box.prop(tool_paths, "ffmpeg_frames")
        box.prop(tool_paths, "ffmpeg_seconds")
        box.prop(tool_paths, "ffmpeg_start_time", text="Start time")
        box.prop(tool_paths, "ffmpeg_end_time", text="End time")

        box.operator( "wm.call_ffmpeg", text="Extract frames" )

        layout.separator()


        props = context.scene.photogrammetry_properties

        box = layout.box()
        box.prop(tool_paths, "colmap_path")
        box.operator( "wm.call_colmap", text="Extract camera poses" )
        
        layout.separator()


        box = layout.box()
        box.prop( props, 'additional_displacement', expand=True )
        box.prop( props, 'additional_rotation', expand=True )
        box.prop( props, 'additional_scale', expand=True )
        box.operator( "wm.create_ref_images", text="Create Ref Images" )

        layout.separator()


        box = layout.box()
        box.label(text="Ref images")
        box.prop( props, 'show_point_cloud', expand=True )
        #box.prop( props, 'index', expand=True )
        box.prop( context.scene.photogrammetry_properties, "camera_images_items", text="Ref. Image" )
        box.operator( "wm.place_camera", text="Place camera" )
        row = box.row()
        row.operator( "wm.decrement_image_index", text="<-" )
        row.operator( "wm.increment_image_index", text="->" )

        index = props.index
        image_props = props.image_pose_properties
        qty = len(image_props)
        if (index >= 0) and (index < qty):
            image_prop = image_props[index]
            box.prop( image_prop, "user_label", text="Img. label" )

        layout.separator()


        box = layout.box()
        box.label(text="Texture paint stencil")
        box.prop( props, 'stencil_scale_adj', expand=True )
        box.operator( "wm.align_stencil", text="Align stencil" )






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


