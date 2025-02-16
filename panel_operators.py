
import bpy
import bmesh
import mathutils
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy_extras.view3d_utils import region_2d_to_vector_3d
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty

import sys
import os

#dir = os.path.dirname(bpy.data.filepath)
#if not dir in sys.path:
#    sys.path.append( dir )

from .panel_properties import *
from .panel_utils      import *
from .panel_async      import *


class MESH_OT_set_mesh_editable( bpy.types.Operator ):
    """
    Mesh is considered editable if vertex coordinates are stored.
    """
    
    bl_idname = "mesh.set_mesh_editable"
    bl_label  = "Pick all selected meshes and put them into the state."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False
        
        return True
    
    
    def execute( self, context ):
        mesh = get_selected_mesh()
        set_mesh_editable( mesh, True )
        return {"FINISHED"}


class MESH_OT_clear_mesh_editable( bpy.types.Operator ):
    """
    Mesh is considered editable if vertex coordinates are stored.
    """
    
    bl_idname = "mesh.clear_mesh_editable"
    bl_label  = "Pick all selected meshes and put them into the state."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False
        
        return True
    
    
    def execute( self, context ):
        mesh = get_selected_mesh()
        set_mesh_editable( mesh, False )
        return {"FINISHED"}



class MESH_OT_apply_transform( bpy.types.Operator ):
    """
    Mesh is considered editable if vertex coordinates are stored.
    """
    
    bl_idname = "mesh.apply_transform"
    bl_label  = "Pick all selected meshes and put them into the state."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False
        
        return True
    
    
    def execute( self, context ):
        mesh = get_selected_mesh()
        recalculate_mesh_shape( mesh )
        return {"FINISHED"}


class MESH_OT_revert_transform( bpy.types.Operator ):
    """
    Mesh is considered editable if vertex coordinates are stored.
    """
    
    bl_idname = "mesh.revert_transform"
    bl_label  = "Pick all selected meshes and put them into the state."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False
        
        return True
    
    
    def execute( self, context ):
        mesh = get_selected_mesh()
        show_original_mesh( mesh )
        return {"FINISHED"}



class MESH_OT_remove_anchors( bpy.types.Operator ):
    """
    Mesh is considered editable if vertex coordinates are stored.
    """
    
    bl_idname = "mesh.remove_anchors"
    bl_label  = "Pick all selected meshes and put them into the state."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False
        
        return True
    
    
    def execute( self, context ):
        mesh = get_selected_mesh()
        remove_selected_anchors( mesh )
        return {"FINISHED"}





class MESH_OT_add_anchors( bpy.types.Operator ):
    """
    Mesh is considered editable if vertex coordinates are stored.
    """
    
    bl_idname = "mesh.add_anchors"
    bl_label  = "Pick all selected meshes and put them into the state."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False
        
        return True
    
    
    def execute( self, context ):
        mesh = get_selected_mesh()
        add_selected_anchors( mesh )
        return {"FINISHED"}



class MESH_OT_apply_radius_to_selected( bpy.types.Operator ):
    """
    Mesh is considered editable if vertex coordinates are stored.
    """
    
    bl_idname = "mesh.apply_radius"
    bl_label  = "Apply radius to all selected pins."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False
        
        return True
    
    
    def execute( self, context ):
        apply_radius_to_selected_pins()
        return {"FINISHED"}




class MESH_OT_apply_metric_to_selected( bpy.types.Operator ):
    """
    Mesh is considered editable if vertex coordinates are stored.
    """
    
    bl_idname = "mesh.apply_metric"
    bl_label  = "Apply metric to all selected pins."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False
        
        return True
    
    
    def execute( self, context ):
        apply_metric_to_selected_pins()
        return {"FINISHED"}








class MESH_OT_reset_selected( bpy.types.Operator ):
    """
    Reset selected pins to default coordinates
    """
    
    bl_idname = "mesh.reset_selected_pins"
    bl_label  = "Reset selected pins to default coordinates."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False
        
        return True
    
    
    def execute( self, context ):
        reset_selected_pins()
        return {"FINISHED"}





class OT_SaveFile(Operator):
    bl_idname = "file.save_pins"
    bl_label = "Save Pins to a File"

    filepath: StringProperty(
        name="File Path",
        description="Path to the file to be saved",
        maxlen=1024,
        default="",
        subtype='FILE_PATH'
    )

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )

    def execute(self, context):
        # Create a dictionary to hold the custom properties
        save_pins( self.filepath )

        print(f"JSON data saved to: {self.filepath}")
        return {'FINISHED'}


    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def check(self, context):
        if not self.filepath.lower().endswith(".json"):
            self.filepath += ".json"
        return True






class OT_OpenFile(Operator, ImportHelper):
    bl_idname = "file.load_pins"
    bl_label = "Open File and Load Pins"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )

    filepath: StringProperty(
        name="File Path",
        description="Path to the file to be opened",
        maxlen=1024,
        default=""
    )
    
    def execute(self, context):
        load_pins( self.filepath )
        print(f"Selected file: {self.filepath}")
        return {'FINISHED'}




# Handler function to track changes
def depsgraph_update_handler(scene):
    # Check if the active object is a mesh in EDIT mode
    if bpy.context.mode != 'EDIT_MESH':
        return

    mesh = get_selected_mesh()
    if mesh is None:
        return

    # Check if a transform operator is running
    wm = bpy.context.window_manager
    active_operator = wm.operators[-1].bl_idname if wm.operators else None

    # Only process after transform operations (translate, rotate, scale)
    if active_operator not in {
        "TRANSFORM_OT_translate",
        "TRANSFORM_OT_rotate",
        "TRANSFORM_OT_resize",  # Resize = Scale
    }:
        return

    # Log or process vertices only at the end of the operation
    #print(f"End of operation: {active_operator}")


    # Access the bmesh for the edit mesh
    bm = bmesh.from_edit_mesh(mesh.data)
    bm.verts.ensure_lookup_table()

    # Check for enabled symmetries.
    #axes = []
    #if mesh.use_mesh_mirror_x:
    #    axes.append(0)
    #if mesh.use_mesh_mirror_y:
    #    axes.append(1)
    #if mesh.use_mesh_mirror_z:
    #    axes.append(2)

    anchor_indices = get_anchor_indices( mesh )

    # Record selected vertices
    inds = []
    did_update = False
    for vert in bm.verts:
        if vert.select:  # Check if the vertex is selected
            index = vert.index
            if index in anchor_indices:
                pos   = vert.co[:]
                # This one either updates the existing one or adds a new one.
                update_mesh_anchor( mesh, index, pos )
                inds.append(index)
                did_update = True

            #verts = find_symmetric_vertices( bm, vert, axes )
            #for vert_i in verts:
            #    index = vert_i.index
            #    if index in anchor_indices:
            #        pos   = vert_i.co[:]
            #        # This one either updates the existing one or adds a new one.
            #        update_mesh_anchor( mesh, index, pos )
            #        inds.append(index)
            #        did_update = True

    if did_update:
        # Update the scene and force redraw
        bpy.context.view_layer.update()  # Update the view layer
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    # Debug: Print the number of displaced vertices
    print(f"Displaced vertices recorded {inds}")












def register_operators():
    bpy.utils.register_class(MESH_OT_set_mesh_editable)
    bpy.utils.register_class(MESH_OT_clear_mesh_editable)
    bpy.utils.register_class(MESH_OT_apply_transform)
    bpy.utils.register_class(MESH_OT_revert_transform)
    bpy.utils.register_class(MESH_OT_add_anchors)
    bpy.utils.register_class(MESH_OT_remove_anchors)
    bpy.utils.register_class(MESH_OT_apply_radius_to_selected)
    bpy.utils.register_class(MESH_OT_apply_metric_to_selected)
    bpy.utils.register_class(MESH_OT_reset_selected)
    bpy.utils.register_class(OT_SaveFile)
    bpy.utils.register_class(OT_OpenFile)

    # Register the depsgraph update handler
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)



def unregister_operators():
    bpy.utils.unregister_class(OT_OpenFile)
    bpy.utils.unregister_class(OT_SaveFile)
    bpy.utils.unregister_class(MESH_OT_reset_selected)
    bpy.utils.unregister_class(MESH_OT_apply_metric_to_selected)
    bpy.utils.unregister_class(MESH_OT_apply_radius_to_selected)
    bpy.utils.unregister_class(MESH_OT_remove_anchors)
    bpy.utils.unregister_class(MESH_OT_add_anchors)
    bpy.utils.unregister_class(MESH_OT_apply_transform)
    bpy.utils.unregister_class(MESH_OT_set_mesh_editable)
    bpy.utils.unregister_class(MESH_OT_clear_mesh_editable)
    bpy.utils.unregister_class(MESH_OT_revert_transform)
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_handler)


