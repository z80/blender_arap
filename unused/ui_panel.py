
bl_info = {
    "name": "Some IGL bindings for mesh manipulation", 
    "author": "z80", 
    "version": (0, 0, 1), 
    "blender": (3, 6, 0), 
    "location": "3D Viewport > Sidebar > 1.21GW", 
    "description": "Some IGL bindings to ease mesh fitting", 
    "category": "Development", 
}



import bpy
import bmesh
import mathutils
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy_extras.view3d_utils import region_2d_to_vector_3d


import sys
import os

#dir = os.path.dirname(bpy.data.filepath)
#if not dir in sys.path:
#    sys.path.append( dir )
    
import install_needed_packages

#import utils
#import utils_working_one

import utils_main


class PanelSettings(bpy.types.PropertyGroup):
    mode_enum : bpy.props.EnumProperty(
        name = "PanelMode", 
        description="Panel mode, either mesh select or addig anchors", 
        items = [("MESH_SELECT", "mesh_select", "Mesh select"), 
                 ("CREATE_ANCHORS", "crate_anchors", "Create anchors"), 
                 ("PICK_VERTICES", "pick_vertices", "Pick vertices")], 
        default='MESH_SELECT'
    )

    symmetry_enum : bpy.props.EnumProperty(
        name = "SymmetryOptions",
        description = "This is a group of checkable buttons",
        items = [('NONE', "none", "Symmetry is disabled"),
                 ('X', "x", "Symmetry X"),
                 ('Y', "y", "Symmetry Y"),
                 ('Z', "z", "Symmetry Z")], 
        default='NONE'
    )

    mesh_name: bpy.props.StringProperty( 
        name="NOTHING", 
        description="The name of the selected mesh"
    )


def get_selected_mesh():
    name = bpy.context.scene.panel_settings.mesh_name
    if not ( name in bpy.context.scene.objects ):
        return None

    mesh = bpy.context.scene.objects[name]
    return mesh


def set_selected_mesh( mesh ):
    if mesh is None:
        name = "NOTHING"

    else:
        name = mesh.name

    bpy.context.scene.panel_settings.mesh_name = name


def get_fixed_verts( mesh ):
    fixed_verts = set( () )

    if 'fixed_verts' in mesh:
        fixed_verts_float = mesh['fixed_verts']
        for vert_ind in fixed_verts_float:
            vert_ind = int( vert_ind )
            fixed_verts.add( vert_ind )

    return fixed_verts


def set_fixed_verts( mesh, fixed_verts ):
    # Convert to float and store in the mesh.
    fixed_verts_float = []
    for vert_ind in fixed_verts:
        vert_ind = float( vert_ind )
        fixed_verts_float.append( vert_ind )

    mesh['fixed_verts'] = fixed_verts_float



class VIEW3D_PT_igl_panel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "1.21 Gigawatt" # Panel top text
    bl_category = "1.21GW" # Sidebar text
    
    bl_idname = "SCENE_PT_igl_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = "scene"
    
    prop_live_update: bpy.props.BoolProperty(
        name="Live mesh update",
        description="If checked, mesh is updated live, else press \"Update\" button",
        default = False
        )


    def draw( self, context ):
        packages_installed = install_needed_packages.check_for_packages()
        if not packages_installed:
            self._ui_need_modules( context )
            
        else:
            #import pdb
            #pdb.set_trace()
            state = bpy.context.scene.panel_settings
            mode = state.mode_enum
            if (mode is None):
                mode = 'MESH_SELECT'
            
            if mode == 'MESH_SELECT':
                self._ui_picking_meshes( context )
                
            elif mode == 'CREATE_ANCHORS':
                mode = bpy.context.active_object.mode
                if mode == 'EDIT':
                    self._ui_fixed_points( context )

                else:
                    self._ui_adding_ref_points( context )

            elif mode == 'PICK_VERTICES':
                self._ui_picking_vertices( context )
 
    
    
    
    def _ui_need_modules( self, context ):
        layout = self.layout

        layout.label( text="Need python modules" )
        layout.label( text="Press the button to install" )
        layout.label( text="If it doesn't work, restart Blender" )
        layout.label( text="and try again..." )

        layout.operator("mesh.igl_install_python_modules", text="Install")
        
            
    
    def _ui_picking_meshes( self, context ):
        layout = self.layout

        layout.label( text="Select a meshes you want to stretch" )
        layout.label( text="and press the button" )
        
        # Create a simple row.
        layout.operator( "mesh.igl_pick_meshes", text="Pick a mesh" )




    def _ui_fixed_points( self, context ):
        layout = self.layout
    
        layout.operator( "mesh.igl_reset", text="Back to picking a mesh" )
      
        layout.label( text="To go back to anchors" )
        layout.label( text="switch to OBJECT mode" )

        layout.label( text="Make selected vertices fixed" )
        layout.operator( "mesh.igl_add_selected_to_fixed", text="Make fixed" )
 
        layout.label( text="Make selected vertices movable" )
        layout.operator( "mesh.igl_remove_selected_from_fixed", text="Make movable" )
 
        layout.label( text="Select all fixed vertices" )
        layout.operator( "mesh.igl_select_fixed", text="Select fixed" )






    def _ui_adding_ref_points( self, context ):
        layout = self.layout
    
        layout.operator( "mesh.igl_reset", text="Back to picking a mesh" )
 
        layout.label( text="To pick fixed vertices" )
        layout.label( text="switch to EDIT mode" )
       
        layout.label( text="Symmetry mode" )
        row = layout.row()
        panel_settings = bpy.context.scene.panel_settings
        row.prop(panel_settings, 'symmetry_enum', expand=True)
        
        layout.label( text="Click to add anchors" )
        layout.operator( "mesh.igl_create_anchor", text="Add an anchor(s)" )
        
        layout.separator()
        # Create a simple row.
        layout.label( text="Apply transform" )
        layout.operator( "mesh.igl_apply_transform", text="Apply" )

        layout.separator()
        # Create a simple row.
        layout.label( text="Show original shape" )
        layout.operator( "mesh.igl_apply_default_shape", text="Show" )

        #layout.label( text="Or return back" )
        #layout.label( text="to picking meshes" )
        #layout.operator( "mesh.igl_switch_to_editing", text="To editing" )



    def _ui_picking_vertices( self, context ):
        layout = self.layout

        layout.label( text="Press ESC to stop picking vertices" )



# Operator installing neede binary python modules.
class MESH_OT_install_python_modules( bpy.types.Operator ):
    """
    Install needed binary modules. Currently they are 
    numpy, scipy, libigl
    """
    
    bl_idname = "mesh.igl_install_python_modules"
    bl_label  = "Install needed python modules: numpy, scipy, libigl"
    
    def execute( self, context ):
        install_needed_packages.install_needed_packages()
        return {"FINISHED"}




# Operator installing needes binary python modules.
class MESH_OT_pick_selected_meshes( bpy.types.Operator ):
    """
    Picks a mesh for further editing.
    """
    
    bl_idname = "mesh.igl_pick_meshes"
    bl_label  = "Pick a mesh and edit them by adding anchors and moving them around."
    
    @classmethod
    def poll( cls, context ):
        selected_meshes = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
        if len(selected_meshes) != 1:
            return False
        
        return True

    
    def execute( self, context ):
        selected_meshes = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
            
        selected_mesh = bpy.types.Mesh( selected_meshes[0] )

        state = bpy.context.scene.panel_settings
        state.mode_enum = 'CREATE_ANCHORS'
        set_selected_mesh( selected_mesh )

        #import pdb
        #pdb.set_trace()

        islands_qty, island_inds, island_default_inds = enum_isolated_islands( selected_mesh )
        Vs, Fs = mesh_2_array( selected_mesh )
        Vs, Fs = to_1d_arrays( Vs, Fs )
        
        selected_mesh["verts"] = Vs
        selected_mesh["faces"] = Fs
        selected_mesh["islands_qty"] = islands_qty
        selected_mesh["island_inds"] = island_inds
        selected_mesh["island_default_inds"] = island_default_inds

        return {"FINISHED"}








# Add selected vertices to fixed vertices list.
class MESH_OT_add_selected_to_fixed( bpy.types.Operator ):
    """
    When selected mesh is in edit mode all selected vertices 
    are added to fixed vertices list.
    """
    
    bl_idname = "mesh.igl_add_selected_to_fixed"
    bl_label  = "Pick all selected vertices and put them into the fixed vertices list."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False

        mode = bpy.context.active_object.mode
        if mode != 'EDIT':
            return False
        
        return True
    
    
    def execute( self, context ):
        mesh = get_selected_mesh()
        bm = bmesh.from_edit_mesh(mesh.data)
    
        # Get the indices of selected vertices
        selected_verts = [v.index for v in bm.verts if v.select]

        fixed_verts = get_fixed_verts( mesh )

        for selected_ind in selected_verts:
            fixed_verts.add( selected_ind )

        set_fixed_verts( mesh, fixed_verts )

        return {"FINISHED"}






# Remove selected vertices from fixed vertices list.
class MESH_OT_remove_selected_from_fixed( bpy.types.Operator ):
    """
    When selected mesh is in edit mode all selected vertices 
    are removed from fixed vertices list.
    """
    
    bl_idname = "mesh.igl_remove_selected_from_fixed"
    bl_label  = "Pick all selected vertices and remove them from fixed vertices_list."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False

        mode = bpy.context.active_object.mode
        if mode != 'EDIT':
            return False
        
        return True
    
    
    def execute( self, context ):
        mesh = get_selected_mesh()
        bm = bmesh.from_edit_mesh(mesh.data)
    
        # Get the indices of selected vertices
        selected_verts = [v.index for v in bm.verts if v.select]

        fixed_verts = get_fixed_verts( mesh )

        for selected_ind in selected_verts:
            fixed_verts.discard( selected_ind )

        set_fixed_verts( mesh, fixed_verts )

        return {"FINISHED"}





# Remove selected vertices from fixed vertices list.
class MESH_OT_select_fixed( bpy.types.Operator ):
    """
    When selected mesh is in edit mode all fixed vertices are selected 
    and movable vertices are unselected.
    """
    
    bl_idname = "mesh.igl_select_fixed"
    bl_label  = "Select all fixed vertices and unselect all movable vertices."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False

        mode = bpy.context.active_object.mode
        if mode != 'EDIT':
            return False
        
        return True
    
    
    def execute( self, context ):
        mesh = get_selected_mesh()
        bm = bmesh.from_edit_mesh(mesh.data)
    
        fixed_verts = get_fixed_verts( mesh )

        print( "fixed_verts: ", fixed_verts )

        #mesh.select_all(action='DESELECT')

        for v in bm.verts:
            index = v.index
            v.select = (index in fixed_verts)

        # Update the mesh to reflect the changes
        bmesh.update_edit_mesh( mesh.data )

        return {"FINISHED"}









# Operator creating an empty axes object which is bound to 
# a vertex of an object.
class MESH_OT_create_anchor( bpy.types.Operator ):
    """
    Pick a point on a mesh by left-clicking it. An axes object should show up.
    Be aware that it only picks vertices with normals towards the camera. You 
    cannot select a vertex on a back side of a mesh.
    """
    
    bl_idname = "mesh.igl_create_anchor"
    bl_label  = "Pick all selected meshes and put them into the state."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        state = bpy.context.scene.panel_settings
        mesh = get_selected_mesh()
        if mesh is None:
            return False
        
        return True
    
    
    def execute( self, context ):
        state = bpy.context.scene.panel_settings
        state.mode_enum = 'PICK_VERTICES'

        bpy.ops.wm.my_mouse_operator('INVOKE_DEFAULT')
        return {"FINISHED"}








class MESH_OT_apply_transform( bpy.types.Operator ):
    """
    Move anchor points around and apply the transform by clicking this button.
    """
    
    bl_idname = "mesh.igl_apply_transform"
    bl_label  = "Apply transform to the meshes selected."
    
    def execute( self, context ):
        import numpy as np
        import igl
        
        #import pdb
        #pdb.set_trace()
        
        state = bpy.context.scene.panel_settings
        mesh = get_selected_mesh()
        anchors = mesh["anchors"]
        # Before adding validate that it still exists.
        existing_anchors = []
        for anchor in anchors:
            if (anchor is not None) and (anchor.name in bpy.context.scene.objects):
                existing_anchors.append( anchor )
        anchors = existing_anchors
        mesh['anchors'] = existing_anchors
        
        Vs = mesh["verts"]
        Fs = mesh["faces"]
        islands_qty = mesh["islands_qty"]
        island_inds_b = list( mesh["island_inds"] )
        island_default_inds_b = list( mesh["island_default_inds"] )

        island_inds = []
        for v in island_inds_b:
            island_inds.append( int(v) )

        island_default_inds = []
        for v in island_default_inds_b:
            island_default_inds.append( int(v) )


        # Get fixed vertex indices.
        fixed_vertices = get_fixed_verts( mesh )

        # Obtain vertex indices from anchors.
        vert_inds = []
        for anchor in anchors:
            vert_ind = anchor["vert_ind"]
            if vert_ind not in fixed_vertices:
                vert_inds.append( vert_ind )

        # Check which islands are involved.
        selected_islands = set(())
        for vert_ind in vert_inds:
            island_ind = island_inds[vert_ind]
            selected_islands.add( island_ind )
        
        # Go over all islands and if not involved, add default vert inds for this island.
        vert_inds_default = []
        for island_ind in range(islands_qty):
  
            if island_ind not in selected_islands:
                base_ind = island_ind * 3
                for i in range(3):
                    vert_ind_in_array = base_ind + i
                    vert_ind = island_default_inds[vert_ind_in_array]
                    if vert_ind not in fixed_vertices:
                        vert_inds_default.append( vert_ind )

        # Aslo add all fixed vertices to the same list.
        for vert_ind in fixed_vertices:
            vert_inds_default.append( vert_ind )

            
        Vs, Fs = to_2d_arrays( Vs, Fs )
        
       
        target_positions = []

        # First, go over real anchors.
        for anchor in anchors:
            at = anchor.matrix_world.translation
            target_positions.append( at )

        # Then, go over default positions so that isolated islands do not deform.
        for vert_ind in vert_inds_default:
            v = Vs[vert_ind]
            target_positions.append( mathutils.Vector( v ) )
            vert_inds.append( vert_ind )
        
        target_positions = np.array( target_positions )

        #import pdb
        #pdb.set_trace()
        fixed_data = []
        qty = target_positions.shape[0]
        for i in range(qty):
            ind = vert_inds[i]
            pos = target_positions[i]
            radius = 1.1 * (i+1)
            metric = "euclidean"
            data = { "index": ind, "pos": pos, "radius": radius, "metric": metric }
            fixed_data.append( data )
        
        #Vs_new = utils.arap_with_varible_normal_importance(Vs, Fs, vert_inds, target_positions )
        Vs_new = utils_main.smooth_transform( Vs, Fs, fixed_data, apply_gp=True, apply_elastic=False, normalized_gp=False )
        
        # Apply modified vertex coordinates to meshes.
        apply_to_mesh( mesh, Vs_new )
        
        return {"FINISHED"}








class MESH_OT_apply_default_shape( bpy.types.Operator ):
    """
    Apply saved transform the mesh had before applying ARAP.
    """
    
    bl_idname = "mesh.igl_apply_default_shape"
    bl_label  = "Apply transform to the meshes selected."
    
    def execute( self, context ):
        import numpy as np
        import igl
        
        #import pdb
        #pdb.set_trace()

        mesh = get_selected_mesh()
       
        Vs = mesh["verts"]
        Fs = mesh["faces"]
        Vs, Fs = to_2d_arrays( Vs, Fs )
        
        # Apply modified vertex coordinates to meshes.
        apply_to_mesh( mesh, Vs )
        
        return {"FINISHED"}







def enum_isolated_islands( mesh ):
    """
    Needs bmesh obtained from a normal mesh in edit mode by doing
    bm = bmesh.new()
    bm.from_mesh(selected_mesh.data)
    """

    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
 
    verts_qty = len(bm.verts)
 
    vertex_islands = []
    apprehended_verts=set(())

    current_vert_ind = 0

    while True:
        
        is_apprehended = current_vert_ind in apprehended_verts
        if is_apprehended:
            current_vert_ind += 1
            if current_vert_ind >= verts_qty:
                break

            continue

        connected_vert_inds = find_connected_vert_inds( bm, current_vert_ind )
        apprehended_verts = apprehended_verts.union( connected_vert_inds )
        vertex_islands.append( connected_vert_inds )

    # Convert islands to lists.
    vertex_island_lists = []
    for island_set in vertex_islands:
        island_list = list( island_set )
        vertex_island_lists.append( island_list )

    # For each island find 3 the most distant points.
    island_default_inds = []
    for island_list in vertex_island_lists:
        inds = find_the_most_distant_point( mesh, island_list, [0] )
        inds = inds[1:]
        inds = find_the_most_distant_point( mesh, island_list, inds )
        inds = find_the_most_distant_point( mesh, island_list, inds )
        island_default_inds.extend( inds )

    # Number of vertex islands.
    islands_qty = len( vertex_islands )


    # Correspondence of a vertex to its island
    island_inds = [i for i in range(verts_qty)]
    for island_ind, island_vert_inds in enumerate(vertex_island_lists):
        for vert_ind in island_vert_inds:
            island_inds[vert_ind] = island_ind


    # Convert indices to float, Blender converts integer arrayy to something peculiar.
    for i, v in enumerate(island_inds):
        island_inds[i] = float(v)

    for i, v in enumerate(island_default_inds):
        island_default_inds[i] = float(v)

    return (islands_qty, island_inds, island_default_inds)



 



def find_connected_vert_inds( bm, vert_ind ):
    """
    Needs bmesh obtained from a normal mesh in edit mode by doing
    bm = bmesh.new()
    bm.from_mesh(selected_mesh.data)
    """
    
    #import pdb
    #pdb.set_trace()
    
    selected_verts=set(())
    vert_inds_to_add = [vert_ind]
    added_data = True
    
    while added_data:
        added_data = False
        
        for vert_ind in vert_inds_to_add:
            if vert_ind not in selected_verts:    
                selected_verts.add( vert_ind )
                added_data = True
        
        if not added_data:
            break
        
        new_vert_inds_to_add = set(())
        for vert_ind in vert_inds_to_add:
            vertex = bm.verts[vert_ind]
    
            # Get all edges connected to the vertex
            connected_edges = vertex.link_edges
    
            connected_vertices = [edge.other_vert(vertex) for edge in connected_edges]
            connected_vert_inds = [ vert.index for vert in connected_vertices ]
            
            for vert_ind in connected_vert_inds:
                if vert_ind not in new_vert_inds_to_add:
                    new_vert_inds_to_add.add( vert_ind )
        
        vert_inds_to_add = new_vert_inds_to_add
    
    #selected_verts = list(selected_verts)
    
    return selected_verts



def find_the_most_distant_point( mesh, island_inds, selected_vert_inds=None ):
    """
    This one looks for the point the most distance from the list of  provided points.
    It appends the list with its index and returns it.
    """
    verts = mesh.data.vertices

    best_dist = 0.0
    best_ind  = None
    
    for sel_vert_ind in island_inds:
        vert = verts[sel_vert_ind]
        sel_co = vert.co

        if selected_vert_inds is None:
            selected_vert_inds = [sel_vert_ind]
            return selected_vert_inds

        accum_dist = 0.0
        for vert_ind in selected_vert_inds:
            vert = verts[vert_ind]
            co = vert.co

            dist = (co - sel_co).length
            accum_dist += dist

        if dist > best_dist:
            best_dist = accum_dist
            best_ind = sel_vert_ind

    selected_vert_inds.append( best_ind )
    return selected_vert_inds



def mesh_2_array( selected_mesh ):
    import numpy as np
    
    bm = bmesh.new()
    bm.from_mesh(selected_mesh.data)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    
    #import pdb
    #pdb.set_trace()

    all_verts = []
    all_faces = []
    
    # only add faces     
    for f in bm.faces:
        face = [v.index for v in f.verts]

        verts_per_face = len(face)
        if verts_per_face == 3:
            sel_face = [ face[0], face[1], face[2]]
            all_faces.append( sel_face )

        elif verts_per_face == 4:
            sel_face = [ face[0], face[1], face[2]]
            all_faces.append( sel_face )
            sel_face = [ face[0], face[2], face[3]]
            all_faces.append( sel_face )

    bm.free()
    
    mat   = selected_mesh.matrix_world
    verts = selected_mesh.data.vertices
    verts_qty = len(verts)
    for vert_ind in range(verts_qty):
        vert = verts[vert_ind]
        co = vert.co
        co = mat @ co
        co = [co.x, co.y, co.z]
        all_verts.append( co )
    
    
    # Convert to numpy arrays
    all_verts = np.array( all_verts )
    all_faces = np.array( all_faces )
    
    return (all_verts, all_faces)




def to_1d_arrays( Vs, Fs ):
    verts_qty = Vs.shape[0]
    faces_qty = Fs.shape[0]
    
    vert_coords = []
    for ind in range(verts_qty):
        x, y, z = Vs[ind, 0], Vs[ind, 1], Vs[ind, 2]
        vert_coords.append( x )
        vert_coords.append( y )
        vert_coords.append( z )
    
    face_vert_inds = []
    for ind in range(faces_qty):
        x, y, z = float(Fs[ind, 0]), float(Fs[ind, 1]), float(Fs[ind, 2])
        face_vert_inds.append( x )
        face_vert_inds.append( y )
        face_vert_inds.append( z )
    
    return (vert_coords, face_vert_inds)





def to_2d_arrays( Vs, Fs ):
    import numpy as np
    
    verts_sz = len(Vs)
    verts = []
    for ind in range( 0, verts_sz, 3 ):
        x = Vs[ind]
        y = Vs[ind+1]
        z = Vs[ind+2]
        
        verts.append( [x, y, z] )
    
    verts = np.array( verts )
    
    
    faces_sz = len(Fs)
    faces = []
    for ind in range( 0, faces_sz, 3 ):
        x = int(Fs[ind])
        y = int(Fs[ind+1])
        z = int(Fs[ind+2])
        
        faces.append( [x, y, z] )
    
    faces = np.array( faces )
    
    return (verts, faces)
        




def apply_to_mesh( mesh, Vs_new ):
    verts = mesh.data.vertices
    verts_qty = Vs_new.shape[0]
    
    #import pdb
    #pdb.set_trace()
    
    mat   = mesh.matrix_world
    inv_mat = mat.inverted()
    
    for vert_ind in range(verts_qty):
        target_at = Vs_new[vert_ind]
        vert = verts[vert_ind]
        co = vert.co
        co.x, co.y, co.z = target_at[0], target_at[1], target_at[2]
        co = inv_mat @ co
        vert.co = co
        #verts[i] = vert



class MESH_OT_reset( bpy.types.Operator ):
    """
    Apply transform to selected meshes.
    """
    
    bl_idname = "mesh.igl_reset"
    bl_label  = "Reset the panel to idle state."
    
    def execute( self, context ):
        #import pdb
        #pdb.set_trace()
        
        s = bpy.context.scene.panel_settings
        s.mode_enum = 'MESH_SELECT'
        set_selected_mesh( None )
        
        return {"FINISHED"}
        





class MyMouseOperator(bpy.types.Operator):
    bl_idname = "wm.my_mouse_operator"
    bl_label = "My Mouse Operator"

    def modal(self, context, event):
        #print( "Entered SimpleMouseOperator" )
        if event.type == 'LEFTMOUSE':  # If we've clicked the left mouse button
            if event.value == 'PRESS':
                print('Left mouse button pressed')
                # Put your custom code here
            elif event.value == 'RELEASE':
                print('Left mouse button released')
                # Or put your custom code here
                self.create_anchor( context, event )
                #return {'CANCELLED'}
                # Don't exit. Only exit on ESC.
                return {'RUNNING_MODAL'}
        
        elif event.type == 'ESC':  # If we've pressed the ESC key
            print( "Returning back to normal UI" )
            state = bpy.context.scene.panel_settings
            state.mode_enum = 'CREATE_ANCHORS'

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    
    def create_anchor( self, context, event ):
        state = bpy.context.scene.panel_settings
        mesh = get_selected_mesh()
        if 'abs_vert_inds' in mesh:
            abs_inds = mesh['abs_vert_inds']
        
        else:
            abs_inds = None

        closest_vert_ind = self.find_closest_vertex( context, event, abs_inds )
        
        if closest_vert_ind < 0:
            return
        
        
        if 'anchors' in mesh:
            anchors = mesh['anchors']
            anchors = list(anchors)
        
        else:
            anchors = []
        
        # Filter out deleted anchors.
        existing_anchors = []
        for anchor in anchors:
            if (anchor is not None) and (anchor.name in bpy.context.scene.objects):
                existing_anchors.append( anchor )
        anchors = existing_anchors
        
        # If there are existing anchors and absolute vertex indices in the mesh, 
        # make sure that the closest selected vertex is in that list. Otherwise, 
        # different anchors are connected to isolated islands. ARAP algorithm is 
        # going to destroy the mesh in that case.
        anchors_qty = len(anchors)
        has_abs_inds = 'abs_vert_inds' in mesh
        if (anchors_qty > 0) and has_abs_inds:
            if closest_vert_ind not in abs_inds:
                return

        vert = mesh.data.vertices[closest_vert_ind]
        
        v = vert.co
        mat = mesh.matrix_world
        loc = mat @ v
        print( "Creating an anchor at ", loc )
        
        ret = bpy.ops.object.empty_add( type='PLAIN_AXES', align='WORLD', location=(loc.x, loc.y, loc.z) )
        anchor = bpy.context.active_object
        anchor.scale = (0.01, 0.01, 0.01)
        
        anchor['mirror'] = None
        anchor['symmetry'] = 'NONE'
        # Store vertex index in the anchor object.
        anchor['vert_ind'] = closest_vert_ind
        
                
        # Add the anchor created to the list of anchors ind store it in the mesh object.
        anchors.append( anchor )

        # Check symmetry.
        symmetry = bpy.context.scene.panel_settings.symmetry_enum
        if symmetry in ['X', 'Y', 'Z']:
            #import pdb
            #pdb.set_trace()

            pos = loc.copy()
            if symmetry == 'X':
                pos.x = -pos.x
            elif symmetry == 'Y':
                pos.y = -pos.y
            else:
                pos.z = -pos.z

            best_vert_ind, world_pos = self.find_closest_vertex_to_a_point( mesh, pos )
            # Make sure that we don't address one and the same vertex.
            if best_vert_ind != closest_vert_ind:
                ret = bpy.ops.object.empty_add( type='PLAIN_AXES', align='WORLD', location=(pos.x, pos.y, pos.z) )
                mirror_anchor = bpy.context.active_object
                mirror_anchor.scale = (0.01, 0.01, 0.01)
                # Store vertex index in the anchor object.
                mirror_anchor['vert_ind'] = best_vert_ind
                mirror_anchor['mirror'] = anchor
                mirror_anchor['symmetry'] = symmetry

                anchor['mirror'] = mirror_anchor
                anchor['symmetry'] = symmetry

                anchors.append( mirror_anchor )

        
        mesh["anchors"] = anchors



    
    
    def find_closest_vertex( self, context, event, abs_inds=None ):
        # Get the 3D view region
        region = context.region
        rv3d = context.region_data

        # Get the mouse position
        coord = mathutils.Vector( (event.mouse_region_x, event.mouse_region_y) )

        # Initialize the minimum distance and the closest vertex
        min_dist = float('inf')
        closest_vertex = None

        state  = bpy.context.scene.panel_settings

        #import pdb
        #pdb.set_trace()
        mesh = get_selected_mesh()
        
        last_best_dist = float('inf')
        
        mouse_ray = self.get_mouse_ray( context, event )
        
        best_vert_ind, best_dist = self.find_closest_vertex_in_a_mesh( region, rv3d, mesh, last_best_dist, coord, mouse_ray, abs_inds )
        
        return best_vert_ind
    
    
    
    def find_closest_vertex_in_a_mesh( self, region, rv3d, mesh, last_best_dist, mouse_at_2d, mouse_ray, abs_inds ):
        
        best_dist = last_best_dist
        best_vert_ind = -1
        
        matrix_world = mesh.matrix_world
        
        inv_matrix_world = matrix_world.to_3x3().transposed()
        mouse_ray_local = inv_matrix_world @ mouse_ray
        
        # If provided, search only within allower vertices.
        if abs_inds is not None:
            vertex_inds = abs_inds
        
        else:
            
            vertex_inds = [ vert_ind for vert_ind, vertex in enumerate( mesh.data.vertices ) ]
            
        # Iterate over all the vertices in the mesh
        for vert_ind in vertex_inds:
            vertex = mesh.data.vertices[vert_ind]            
            # Transform the vertex coordinates to 2D
            norm = vertex.normal
            
            # Check if normal is towards the camera.
            # Dot product should be negative.
            d = norm.dot( mouse_ray_local )
            if d >= 0.0:
                continue
            
            loc3d = matrix_world @ vertex.co
            loc2d = location_3d_to_region_2d( region, rv3d, loc3d )
            # It can return None, if the vertex is behind the camera.
            # And it indeed may happen because I iterate over all vertices here.
            if loc2d is None:
                continue

            # Calculate the distance to the mouse position
            dist = ( loc2d - mouse_at_2d ).length

            # If this vertex is closer, update the minimum distance and the closest vertex
            if dist < best_dist:
                best_dist     = dist
                best_vert_ind = vert_ind
        
        return best_vert_ind, best_dist
    
    
    
    def get_mouse_ray( self, context, event ):
        # Get the 3D view region
        region = context.region
        rv3d   = context.region_data

        # Get the mouse position
        coord = event.mouse_region_x, event.mouse_region_y

        # Calculate the 3D vector
        ray_vector = region_2d_to_vector_3d( region, rv3d, coord )
        
        ray_vector = ray_vector.normalized()

        return ray_vector
    
    
    
    def find_closest_vertex_to_a_point( self, mesh, point ):
    
        matrix_world = mesh.matrix_world
        
        inv_matrix_world = matrix_world.inverted()
        point_local = inv_matrix_world @ point
        
        last_best_dist = float('inf')
        last_best_ind  = -1
        world_pos = None

        vertex_inds = [ vert_ind for vert_ind, vertex in enumerate( mesh.data.vertices ) ]
            
        # Iterate over all the vertices in the mesh
        for vert_ind in vertex_inds:
            vertex = mesh.data.vertices[vert_ind]
            vertex_pos = vertex.co

            # Calculate the distance to the mouse position
            dist = ( vertex_pos - point_local ).length

            # If this vertex is closer, update the minimum distance and the closest vertex
            if dist < last_best_dist:
                last_best_dist = dist
                last_best_ind  = vert_ind
                world_pos = matrix_world @ vertex_pos
        
        return last_best_ind, world_pos




def on_transform_completed(obj, scene):
    if (obj.type != 'EMPTY'):
        return

    has_mirror = 'mirror' in obj
    if not has_mirror:
        return

    mirror = obj['mirror']
    
    if mirror is None:
        obj['symmetry'] = 'NONE'
        return
    
    symmetry = obj['symmetry']

    loc = obj.location.copy()
    if symmetry == 'X':
        loc.x = -loc.x
    elif symmetry == 'Y':
        loc.y = -loc.y
    elif symmetry == 'Z':
        loc.z = -loc.z
    mirror.location = loc

    print("Transform Completed")

def on_depsgraph_update(scene, depsgraph):
    if on_depsgraph_update.operator is None:
        on_depsgraph_update.operator = bpy.context.active_operator
        return

    if on_depsgraph_update.operator == bpy.context.active_operator:
        return

    on_depsgraph_update.operator = None  # Reset now to not trigger recursion in next step in case it triggers a depsgraph update
    obj = bpy.context.active_object
    on_transform_completed(obj, scene)













def register():
    bpy.utils.register_class(PanelSettings)
    bpy.types.Scene.panel_settings = bpy.props.PointerProperty(type=PanelSettings)
    
    bpy.utils.register_class(VIEW3D_PT_igl_panel)
    bpy.utils.register_class(MESH_OT_install_python_modules)
    bpy.utils.register_class(MESH_OT_pick_selected_meshes)
    bpy.utils.register_class(MESH_OT_add_selected_to_fixed)
    bpy.utils.register_class(MESH_OT_remove_selected_from_fixed)
    bpy.utils.register_class(MESH_OT_select_fixed)
    bpy.utils.register_class(MESH_OT_create_anchor)
    bpy.utils.register_class(MESH_OT_apply_transform)
    bpy.utils.register_class(MESH_OT_apply_default_shape)
    bpy.utils.register_class(MESH_OT_reset)
    
    # Make blender call on_depsgraph_update after each
    # update of Blender's internal dependency graph
    on_depsgraph_update.operator = None
    bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)
    
    bpy.utils.register_class(MyMouseOperator)
    #bpy.ops.wm.my_mouse_operator('INVOKE_DEFAULT')


def unregister():
    bpy.utils.unregister_class(SimpleMouseOperator)
    # Make blender call on_depsgraph_update after each
    # update of Blender's internal dependency graph
    bpy.app.handlers.depsgraph_update_post.erase(on_depsgraph_update)

    bpy.utils.unregister_class(MESH_OT_install_python_modules)
    bpy.utils.unregister_class(MESH_OT_pick_selected_meshes)
    bpy.utils.unregister_class(MESH_OT_add_selected_to_fixed)
    bpy.utils.unregister_class(MESH_OT_remove_selected_from_fixed)
    bpy.utils.unregister_class(MESH_OT_select_fixed)
    bpy.utils.unregister_class(MESH_OT_create_anchor)
    bpy.utils.unregister_class(MESH_OT_apply_transform)
    bpy.utils.unregister_class(MESH_OT_apply_default_shape)
    bpy.utils.unregister_class(MESH_OT_reset)
    
    bpy.utils.unregister_class(VIEW3D_PT_igl_panel)
    
    bpy.utils.unregister_class(AnchorSymmetry)
    


if __name__ == "__main__":
    register()
