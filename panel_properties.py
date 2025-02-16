
import bpy

import sys
import os
from collections import deque

#dir = os.path.dirname(bpy.data.filepath)
#if not dir in sys.path:
#    sys.path.append( dir )

class MeshVertexProp(bpy.types.PropertyGroup):
    pos: bpy.props.FloatVectorProperty(
        name="Position",
        description="3D vector",
        size=3,  # 3 components for XYZ
        default=(0.0, 0.0, 0.0),
        subtype='XYZ'  # Display as a 3D vector
    )

class AnchorPointProp(bpy.types.PropertyGroup):
    metric: bpy.props.EnumProperty(
        name="Metric", 
        description="Distance metric", 
        items=[
            ('euclidean', 'Euclidean', 'Euclidean distance metric'), 
            ('geodesic',  'Geodesic',  'Geodesic distance metric')
        ], 
        default='euclidean'
    )

    radius: bpy.props.FloatProperty( 
        name='Radius', 
        description='Influence radius of this anchor point', 
        default=0.1, 
        min=0.0001
    )

    index: bpy.props.IntProperty( 
        name='index', 
        description='Vertex index of the anchor point', 
        default=0, 
        min=0
    )

    pos: bpy.props.FloatVectorProperty(
        name="Position",
        description="3D vector",
        size=3,  # 3 components for XYZ
        default=(0.0, 0.0, 0.0),
        subtype='XYZ'  # Display as a 3D vector
    )


def _update_draw_operator(self, context):
    bpy.ops.view3d.draw_red_markers('INVOKE_DEFAULT')



class MeshProp(bpy.types.PropertyGroup):
    original_shape: bpy.props.CollectionProperty(type=MeshVertexProp)
    
    anchors: bpy.props.CollectionProperty(type=AnchorPointProp)

    step_1: bpy.props.EnumProperty(
        name="First step", 
        description="First processing step", 
        items=[
            ('inverse_dist',  'Inverse distance', 'Inverse Distance'), 
            ('gaussian_proc', 'Gaussian process',  'Gaussian Process')
        ], 
        default='inverse_dist'
    )

    apply_rigid_transform: bpy.props.BoolProperty( 
        name="Rigid Transform", 
        description="Should rigid transform be applied to all vertices prior to elastic transform", 
        default=False
    )

    # One common settings is decay radius
    decay_radius: bpy.props.FloatProperty(
        name="Decay Radius",
        description="Decay Radius Value. It defines how the whole transformation influence decays over distance",
        default=0.2
    )


    # Individual settings for the transformations.
    # Gaussian process has this one setting.
    gp_regularization: bpy.props.FloatProperty(
        name="Gaussian Process Regularization",
        description="Gaussian Process Regularization value",
        default=1.0e-6
    )

    # Inverse distance has two.
    id_epsilon: bpy.props.FloatProperty(
        name="Inverse Distance Epsilon",
        description="Inverse Distance Epsilon Value",
        default=1.0e-6
    )
    
    # Inverse distance power
    id_power: bpy.props.IntProperty( 
        name='Inverse Distance Power', 
        description='Inverse Distance Power value', 
        default=2, 
        min=1
    )

    step_2: bpy.props.EnumProperty(
        name="Second step", 
        description="Second processing step", 
        items=[
            ('none',    'None',                'No 2-d step'), 
            ('elastic', 'Elastic deformation', 'Elastic deformation transformation')
        ], 
        default='none'
    )

    normal_importance: bpy.props.FloatProperty(
        name="Normal Importance", 
        description="How much normal direction is more important than tangential direction. Do not use too large values, it gets unstable for values greater than 4.", 
        default = 1.0, 
        min = 0.01
    )

    num_iterations: bpy.props.IntProperty( 
        name='Elastic Iterations', 
        description='How many iterations the elastic deformation computation takes. The bigger the number, the closer it is to the true elastic fabric.', 
        default=1, 
        min=1
    )

    step_3: bpy.props.EnumProperty(
        name="Third step", 
        description="Third processing step", 
        items=[
            ('none',    'None',                'No 3-d step'), 
            ('proportional_falloff', 'Proportional Falloff', 'Proportional Falloff between Gaussian Process and Elastic Defirmation.')
        ], 
        default='none'
    )


    draw_pins: bpy.props.BoolProperty( 
        name="Draw Pins", 
        description="Should draw red dots for all the pins", 
        default=True, 
        update=_update_draw_operator
    )










# Define a property group to store paths
class ToolProperties(bpy.types.PropertyGroup):
    colmap_path: bpy.props.StringProperty(
        name="COLMAP Path",
        description="Path to the COLMAP executable",
        default="", 
        subtype="FILE_PATH"
    )
    ffmpeg_path: bpy.props.StringProperty(
        name="FFmpeg Path",
        description="Path to the FFmpeg executable",
        default="", 
        subtype="FILE_PATH"
    )

    ffmpeg_frames: bpy.props.FloatProperty( 
        name='Frames', 
        description='Number of frames', 
        default=1.0, 
        min=0.0001
    )

    ffmpeg_seconds: bpy.props.FloatProperty( 
        name='Per Seconds', 
        description='Number of seconds', 
        default=1.0, 
        min=0.0001
    )

    ffmpeg_start_time: bpy.props.FloatProperty( 
        name='Start time in seconds', 
        description='Where in the video start extracting frames, <=0 for the beginning of the video', 
        default=-1.0, 
        min=-1.0
    )

    ffmpeg_end_time: bpy.props.FloatProperty( 
        name='End time in seconds', 
        description='Where in the video stop extracting frames, -1 for the end of the video', 
        default=-1.0, 
        min=-1.0
    )

    ffmpeg_scale_percentage: bpy.props.FloatProperty( 
        name='Image Scale Percentage', 
        description='What the extracted image size whould be compared to the video resolution', 
        default=100.0, 
        min=1.0
    )









def register_properties():
    # Register the property group
    bpy.utils.register_class(ToolProperties)
    bpy.types.Scene.tool_paths = bpy.props.PointerProperty(type=ToolProperties)

    bpy.utils.register_class(MeshVertexProp)
    bpy.utils.register_class(AnchorPointProp)
    bpy.utils.register_class(MeshProp)
    
    bpy.types.Mesh.mesh_prop = bpy.props.PointerProperty(type=MeshProp)


def unregister_properties():
    # Remove the PointerProperty from the Mesh type
    del bpy.types.Mesh.mesh_prop

    bpy.utils.unregister_class(MeshProp)
    bpy.utils.unregister_class(AnchorPointProp)
    bpy.utils.unregister_class(MeshVertexProp)

    bpy.utils.unregister_class(MyProperties)
    del bpy.types.Scene.tool_paths





