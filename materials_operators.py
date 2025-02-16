
import bpy

from .panel_utils     import *
from .materials_utils import *

class MaterialProps(bpy.types.PropertyGroup):
    resolution: bpy.props.IntProperty( 
        name='Resolution', 
        description='Texture resolution', 
        default=1024, 
        min=8
    )

    udim: bpy.props.BoolProperty(
        name="Use UDIM",
        description="If yes, uses UDIM material and texture naming, and X,Y indices otherwise",
        default=True
    )


class MESH_OT_CreateUDIMMaterials( bpy.types.Operator ):
    """
    Create UDIM materials for the selected mesh.
    """
    
    bl_idname = "mesh.create_udim_materials"
    bl_label  = "Create UDIM materials for the selected mesh."
    
    @classmethod
    def poll( cls, context ):
        # There should be a mesh in the consideration.
        mesh = get_selected_mesh()
        if mesh is None:
            return False
        
        return True
    
    
    def execute( self, context ):
        scene = context.scene
        props = scene.material_props
        resolution = props.resolution
        use_udim   = props.udim
        create_udim_materials( texture_path="./textures", resolution=resolution, use_udim=use_udim )
        return {"FINISHED"}


class MESH_PT_UDIMMaterialsPanel(bpy.types.Panel):
    bl_label = "UDIM Materials"
    bl_idname = "VIEW3D_PT_udim_materials_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UDIM Materials"

    def draw(self, context):
        layout = self.layout

        mesh = get_selected_mesh()
        if mesh is None:
            layout.label( text="Select a mesh" )
            return
        scene = context.scene
        layout.prop( scene.material_props, 'resolution', text="Resolution" )
        layout.prop( scene.material_props, 'udim',       text="Use UDIM" )
        layout.operator("mesh.create_udim_materials", text="Create New Material(s)")




def materials_register():
    # Register the property group
    bpy.utils.register_class(MaterialProps)
    bpy.utils.register_class(MESH_OT_CreateUDIMMaterials)
    bpy.types.Scene.material_props = bpy.props.PointerProperty(type=MaterialProps)
    bpy.utils.register_class(MESH_PT_UDIMMaterialsPanel)

def materials_unregister():
    bpy.utils.unregister_class(MESH_PT_UDIMMaterialsPanel)
    bpy.utils.unregister_class(MaterialProps)
    bpy.utils.unregister_class(MESH_OT_CreateUDIMMaterials)
    del bpy.types.Scene.material_props


