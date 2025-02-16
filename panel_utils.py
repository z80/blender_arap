
import bpy
import bmesh
import mathutils
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy_extras.view3d_utils import region_2d_to_vector_3d


import sys
import os
import json

import numpy as np

#dir = os.path.dirname(bpy.data.filepath)
#if not dir in sys.path:
#    sys.path.append( dir )

from .panel_properties import *


def get_selected_mesh():
    # Get all selected objects
    selected_objects = bpy.context.selected_objects

    for obj in selected_objects:
        # Check if the object is a mesh
        if obj.type == 'MESH':
            return obj

    return None



def get_anchor_coordinates():
    """
    This is for drawing markers.
    """
    mesh = get_selected_mesh()
    if mesh is None:
        return []

    mesh_prop = mesh.data.mesh_prop

    draw_pins = mesh_prop.draw_pins
    if not draw_pins:
        return []

    anchors   = mesh_prop.anchors
    qty = len(anchors)
    if qty < 1:
        return []

    #region_data = bpy.context.region_data
    #inv_M_view = region_data.view_matrix.to_3x3().transposed()
    #M_mesh = mesh.matrix_world.to_3x3()
    #M_adj  = inv_M_view @ M_mesh
    
    world_matrix = np.array( mesh.matrix_world )
    
    positions = []
    for anchor in anchors:
        #vertex_index = anchor.index
        #vertex_normal = mesh.data.vertices[vertex_index].normal
        #vertex_normal = M_adj @ vertex_normal
        #if vertex_normal.y >= -0.5:
        #    pos = anchor.pos
        #    positions.append( pos )
        pos = anchor.pos
        positions.append( pos )


    positions = np.array( positions )
    ones = np.ones( (positions.shape[0], 1) )
    homogeneous_coords = np.concatenate( (positions, ones), axis=1 )

    world_coords = homogeneous_coords @ world_matrix.T
    world_coords = world_coords[:, :3]

    # Need to turn it into the list of tuples.
    qty = world_coords.shape[0]
    list_of_coords = []
    for i in range(qty):
        list_of_coords.append( (float(world_coords[i,0]), float(world_coords[i,1]), float(world_coords[i,2]) ) )

    return list_of_coords




def get_mesh_editable( mesh ):
    mesh_prop = mesh.data.mesh_prop
    original_shape = mesh_prop.original_shape
    stored_qty = len(original_shape)

    verts_qty = len(mesh.data.vertices)

    ret = (stored_qty == verts_qty)

    return ret




def set_mesh_editable( mesh, en ):
    if en:
        store_mesh_vertices( mesh )

    else:
        mesh_prop = mesh.data.mesh_prop
        original_shape = mesh_prop.original_shape

        original_shape.clear()



def mesh_to_2d_arrays( mesh ):
    vertices = np.array([v.co for v in mesh.data.vertices])

    # Extract and virtually triangulate faces
    virtual_faces = []
    for poly in mesh.data.polygons:
        verts = poly.vertices[:]
        if len(verts) == 3:
            # If the polygon is already a triangle, use it as-is
            virtual_faces.append(verts)
        elif len(verts) > 3:
            # Triangulate the polygon
            qty = len(verts)
            for i in range(qty):
                virtual_faces.append((verts[i], verts[(i+1)%qty], verts[(i+2)%qty]))

    virtual_faces = np.array(virtual_faces)

    return vertices, virtual_faces



def store_mesh_vertices( mesh ):
    mesh_prop = mesh.data.mesh_prop
    original_shape = mesh_prop.original_shape

    original_shape.clear()

    Vs, Fs = mesh_to_2d_arrays( mesh )
    for vertex in Vs:
        new_vertex = original_shape.add()
        new_vertex.pos = vertex



def get_mesh_original_data( mesh ):
    mesh_prop = mesh.data.mesh_prop
    original_shape = mesh_prop.original_shape

    verts = []
    Vs, Fs = mesh_to_2d_arrays( mesh )

    for index, vertex in enumerate(original_shape):
        pos = vertex.pos
        Vs[index,0] = pos[0]
        Vs[index,1] = pos[1]
        Vs[index,2] = pos[2]

    return Vs, Fs





def add_mesh_anchor( mesh, index, pos ):
    mesh_prop = mesh.data.mesh_prop
    anchors   = mesh_prop.anchors

    for anchor in anchors:
        existing_index = anchor.index
        if index == existing_index:
            anchor.pos = pos[:]
            return

    anchor = anchors.add()
    anchor.index = index
    anchor.pos   = pos[:]



def get_anchor_indices( mesh ):
    mesh_prop = mesh.data.mesh_prop
    anchors   = mesh_prop.anchors
    
    indices = set()
    for anchor in anchors:
        index = anchor.index
        indices.add( index )

    return indices


def update_mesh_anchor( mesh, index, pos ):
    mesh_prop = mesh.data.mesh_prop
    anchors   = mesh_prop.anchors

    for anchor in anchors:
        existing_index = anchor.index
        if index == existing_index:
            anchor.pos = pos[:]




def add_selected_anchors( mesh ):
    """
    Add selected vertices to the list of anchors.
    """
    # Check if the active object is a mesh in EDIT mode
    if bpy.context.mode != 'EDIT_MESH':
        return

    mesh = get_selected_mesh()
    if mesh is None:
        return

    is_editable = get_mesh_editable( mesh )
    if not is_editable:
        return

    anchor_indices = get_anchor_indices( mesh )

    # Access the bmesh for the edit mesh
    bm = bmesh.from_edit_mesh(mesh.data)
    bm.verts.ensure_lookup_table()

    # Record selected vertices
    inds = []
    for vert in bm.verts:
        if vert.select:  # Check if the vertex is selected
            index = vert.index
            if index not in anchor_indices:
                pos = vert.co
                add_mesh_anchor( mesh, index, pos )
    
    # Execute drawing markers.
    bpy.ops.view3d.draw_red_markers('INVOKE_DEFAULT')

    # Update the scene and force redraw
    bpy.context.view_layer.update()  # Update the view layer
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()



def remove_mesh_anchor( mesh, index ):
    mesh_prop = mesh.data.mesh_prop
    anchors   = mesh_prop.anchors

    for idx, anchor in enumerate(anchors):
        existing_index = anchor.index
        if index == existing_index:
            anchors.remove(idx)
            return




def remove_selected_anchors( mesh ):
    """
    Removes selected vertices from the list of anchors.
    """
    # Check if the active object is a mesh in EDIT mode
    if bpy.context.mode != 'EDIT_MESH':
        return

    mesh = get_selected_mesh()
    if mesh is None:
        return

    is_editable = get_mesh_editable( mesh )
    if not is_editable:
        return

    # Access the bmesh for the edit mesh
    bm = bmesh.from_edit_mesh(mesh.data)
    bm.verts.ensure_lookup_table()

    # Record selected vertices
    inds = []
    for vert in bm.verts:
        if vert.select:  # Check if the vertex is selected
            index = vert.index
            remove_mesh_anchor( mesh, index )

    # Update the scene and force redraw
    bpy.context.view_layer.update()  # Update the view layer
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()




def get_selected_anchor_index():
    # Check if the active object is a mesh in EDIT mode
    if bpy.context.mode != 'EDIT_MESH':
        return -1

    mesh = get_selected_mesh()
    if mesh is None:
        return -1

    is_editable = get_mesh_editable( mesh )
    if not is_editable:
        return -1

    # Access the bmesh for the edit mesh
    bm = bmesh.from_edit_mesh(mesh.data)
    bm.verts.ensure_lookup_table()

    # Record selected vertices
    indices = set()
    for vert in bm.verts:
        if vert.select:  # Check if the vertex is selected
            index = vert.index
            indices.add( index )

    # Check if such anchor exists
    mesh_prop = mesh.data.mesh_prop
    anchors   = mesh_prop.anchors
    for idx, anchor in enumerate(anchors):
        anchor_index = anchor.index
        if anchor_index in indices:
            return idx

    return -1




def get_selected_anchor():
    # Check if the active object is a mesh in EDIT mode
    if bpy.context.mode != 'EDIT_MESH':
        return None

    mesh = get_selected_mesh()
    if mesh is None:
        return None

    is_editable = get_mesh_editable( mesh )
    if not is_editable:
        return None

    # Access the bmesh for the edit mesh
    bm = bmesh.from_edit_mesh(mesh.data)
    bm.verts.ensure_lookup_table()

    # Record selected vertices
    indices = set()
    for vert in bm.verts:
        if vert.select:  # Check if the vertex is selected
            index = vert.index
            indices.add( index )

    # Check if such anchor exists
    mesh_prop = mesh.data.mesh_prop
    anchors   = mesh_prop.anchors
    for idx, anchor in enumerate(anchors):
        anchor_index = anchor.index
        if anchor_index in indices:
            return anchor

    return None



def get_all_selected_anchors():
    # Check if the active object is a mesh in EDIT mode
    if bpy.context.mode != 'EDIT_MESH':
        return []

    mesh = get_selected_mesh()
    if mesh is None:
        return []

    is_editable = get_mesh_editable( mesh )
    if not is_editable:
        return []

    # Access the bmesh for the edit mesh
    bm = bmesh.from_edit_mesh(mesh.data)
    bm.verts.ensure_lookup_table()

    # Record selected vertices
    indices = set()
    for vert in bm.verts:
        if vert.select:  # Check if the vertex is selected
            index = vert.index
            indices.add( index )

    # Check if such anchor exists
    mesh_prop = mesh.data.mesh_prop
    anchors   = mesh_prop.anchors
    selected_anchors = []
    for idx, anchor in enumerate(anchors):
        anchor_index = anchor.index
        if anchor_index in indices:
            selected_anchors.append( anchor )

    return selected_anchors




def reset_selected_pins():
    """
    Restore coordinates of selected anchors to what they were 
    in unmodified mesh.
    """

    mesh = get_selected_mesh()
    if mesh is None:
        return

    shape = mesh.data.mesh_prop.original_shape

    anchors = get_all_selected_anchors()
    for anchor in anchors:
        index = anchor.index
        vert_data = shape[index]
        pos = vert_data.pos
        anchor.pos = ( pos[0], pos[1], pos[2] )

    # Update the scene and force redraw
    bpy.context.view_layer.update()  # Update the view layer
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()



def serialize_pins():
    """
    All pins -> JSON.
    """

    mesh = get_selected_mesh()
    if mesh is None:
        return

    
    anchors = mesh.data.mesh_prop.anchors
    data = []
    for anchor in anchors:
        pos    = anchor.pos[:]
        index  = anchor.index
        radius = anchor.radius
        metric = anchor.metric
        item = { "pos": pos, "index": index, "radius": radius, "metric": metric }
        data.append( item )

    return data


def save_pins( file_name ):
    data = serialize_pins()
    data_stri = json.dumps( data, indent=4 )
    with open( file_name, "w" ) as file:
        file.write( data_stri )
        



def deserialize_pins( data ):
    """
    JSON -> all pins.
    """

    mesh = get_selected_mesh()
    if mesh is None:
        return None

    mode_save = bpy.context.object.mode
    # Switch to object mode.
    bpy.ops.object.mode_set(mode='OBJECT') 

    anchors = mesh.data.mesh_prop.anchors
    anchors.clear()
    for item in data:
        anchor = anchors.add()
        anchor.pos    = item["pos"]
        anchor.index  = item["index"]
        anchor.radius = item["radius"]
        anchor.metric = item["metric"]

    bpy.ops.object.mode_set(mode=mode_save) 


def load_pins( file_name ):
    #import pdb
    #pdb.set_trace()

    with open( file_name, "r" ) as file:
        data_stri = file.read()
        data = json.loads( data_stri )

    if data is not None:
        deserialize_pins( data )






# Function to find symmetric counterpart
def find_symmetric_vertices(bm, vert, axes):
    """Find the symmetric counterpart of a vertex along the specified axis."""
    # Create a mirrored position
    mirrored_verts = [vert]
    for axis in axes:
        # Find a vertex in the mesh with the same position
        for vert in mirrored_verts:
            mirrored_pos = vert.co.copy()
            mirrored_pos[axis] = -mirrored_pos[axis]
            for other_vert in bm.verts:
                if (not other_vert.select) and (other_vert.co == mirrored_pos) and (not other_vert in mirrored_verts):
                    mirrored_verts.append( other_vert )

    return mirrored_verts


def get_mesh_update_data( mesh ):
    V, F = get_mesh_original_data( mesh )

    mesh_prop = mesh.data.mesh_prop
    anchors   = mesh_prop.anchors
    
    qty = len(anchors)
    update_data = []

    qty = 0
    radius_accum = 0.0
    for anchor in anchors:
        index  = anchor.index
        pos    = anchor.pos
        metric = anchor.metric
        radius = anchor.radius
        data = { 'index': index, 'pos': pos, 'metric': metric, 'radius': radius }
        radius_accum += radius
        qty += 1
        update_data.append( data )

    use_algorithm = mesh_prop.step_1
    step_2            = mesh_prop.step_2 != 'none'
    normal_importance = mesh_prop.normal_importance
    num_iterations    = mesh_prop.num_iterations
    step_3            = mesh_prop.step_3 != 'none'
    rigid_transform   = mesh.data.mesh_prop.apply_rigid_transform
    decay_radius      = mesh.data.mesh_prop.decay_radius
    gp_radius         = radius_accum / qty
    gp_regularization = mesh.data.mesh_prop.gp_regularization
    id_power          = mesh.data.mesh_prop.id_power
    id_epsilon        = mesh.data.mesh_prop.id_epsilon

    return V, F, update_data, use_algorithm, step_2, normal_importance, num_iterations, step_3, rigid_transform, decay_radius, gp_radius, gp_regularization, id_power, id_epsilon



def apply_to_mesh( mesh, V_new ):
    #unselect_all_vertices( mesh )

    verts = mesh.data.vertices
    verts_qty = V_new.shape[0]
    
    #import pdb
    #pdb.set_trace()

    # Store the current mode.
    mode_save = bpy.context.object.mode
    # Switch to object mode.
    bpy.ops.object.mode_set(mode='OBJECT')

    
    mat   = mesh.matrix_world
    inv_mat = mat.inverted()
    
    for vert_ind in range(verts_qty):
        target_at = V_new[vert_ind]
        vert = verts[vert_ind]
        vert.co = (target_at[0], target_at[1], target_at[2])

    # Restore the saved mode.
    bpy.ops.object.mode_set(mode=mode_save)



def show_original_mesh( mesh ):
    #unselect_all_vertices( mesh )

    verts = mesh.data.vertices
    verts_qty = len(verts)

    mesh_prop = mesh.data.mesh_prop
    original_shape = mesh_prop.original_shape
    
    # Store the current mode.
    mode_save = bpy.context.object.mode
    print( "Saved mode: ", mode_save )
    # Switch to object mode.
    bpy.ops.object.mode_set(mode='OBJECT')

    for vert_ind in range(verts_qty):
        target  = original_shape[vert_ind].pos
        vert    = verts[vert_ind]
        vert.co = target

    # Restore the saved mode.
    bpy.ops.object.mode_set(mode=mode_save)


def unselect_all_vertices(obj):
    """
    Unselect all vertices of the mesh in Edit Mode.
    
    :param obj: The mesh object (must be in Edit Mode).
    """
    #if bpy.context.mode != 'EDIT_MESH':
    #    raise RuntimeError("The object must be in Edit Mode to unselect vertices.")
    
    if bpy.context.mode == 'EDIT_MESH':
        # Access the BMesh of the object
        bm = bmesh.from_edit_mesh(obj.data)
    
        # Deselect all vertices
        for vert in bm.verts:
            vert.select = False
    
        # Update the mesh in the viewport
        bmesh.update_edit_mesh(obj.data, loop_triangles=False)



def apply_radius_to_selected_pins():
    #import pdb
    #pdb.set_trace()
    # Pick radius from the very first pin selected and apply to all other ones.
    selected_anchor = get_selected_anchor()

    selected_anchors = get_all_selected_anchors()
    radius = selected_anchor.radius

    for anchor in selected_anchors:
        anchor.radius = radius

def apply_metric_to_selected_pins():
    # Pick radius from the very first pin selected and apply to all other ones.
    selected_anchor = get_selected_anchor()

    selected_anchors = get_all_selected_anchors()
    metric = selected_anchor.metric

    for anchor in selected_anchors:
        anchor.metric = metric


