
import bpy
import mathutils
import bpy_extras.view3d_utils as v3du

from .utils_photogrammetry import *

def _project_to_screen(vector, region, rv3d):
    return v3du.location_3d_to_region_2d(region, rv3d, vector)

def _get_3d_viewport_region():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    return region, area.spaces[0].region_3d
    return None, None

def _get_reference_image(obj):
    if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
        return obj.data

    return None

def align_stencil_to_viewport():
    #import pdb
    #pdb.set_trace()
    index = bpy.context.scene.photogrammetry_properties.index
    hide_all_images()

    prop = bpy.context.scene.photogrammetry_properties.image_pose_properties[index]
    object_name = prop.object_name

    obj = bpy.data.objects.get( object_name )
    reference_image = _get_reference_image(obj)
    reference_aspect_ratio = reference_image.size[0] / reference_image.size[1]
    
    if not reference_image:
        print("Reference image not found")
        return
    
    region, rv3d = _get_3d_viewport_region()
    
    if not region or not rv3d:
        print("3D viewport region not found")
        return
    
    # Get the corners of the reference image in object space
    s = 1.0/reference_aspect_ratio
    ref_corners = [
        mathutils.Vector((-0.5, -0.5*s, 0.0)),  # Bottom-left
        mathutils.Vector((0.5, -0.5*s, 0.0)),   # Bottom-right
        mathutils.Vector((0.5, 0.5*s, 0.0)),    # Top-right
        mathutils.Vector((-0.5, 0.5*s, 0.0)),   # Top-left
    ]
    
    # Transform corners to world space
    ref_corners_world = [obj.matrix_world @ corner for corner in ref_corners]
    
    # Project corners to screen space
    ref_corners_screen = [_project_to_screen(corner, region, rv3d) for corner in ref_corners_world]
    
    # Calculate the bounding box in screen space
    min_x = min(corner.x for corner in ref_corners_screen)
    max_x = max(corner.x for corner in ref_corners_screen)
    min_y = min(corner.y for corner in ref_corners_screen)
    max_y = max(corner.y for corner in ref_corners_screen)
    
    # Calculate width and height in screen space
    screen_width = max_x - min_x
    screen_height = max_y - min_y
    
    # Set up stencil image
    version = bpy.app.version
    if version[0] == 4:
        if version[1] < 2:
            brush = bpy.context.tool_settings.image_paint.brush
            brush.texture = bpy.data.textures.new(name="StencilTexture", type='IMAGE')
            brush.texture.image = reference_image
            brush.texture_slot.map_mode = 'STENCIL'

            # Adjust stencil image scale and offset to match screen dimensions while maintaining aspect ratio
            screen_aspect_ratio = screen_width / screen_height
            if reference_aspect_ratio > screen_aspect_ratio:
                scale_x = screen_width / reference_image.size[0]
                scale_y = scale_x / reference_aspect_ratio
            else:
                scale_y = screen_height / reference_image.size[1]
                scale_x = scale_y * reference_aspect_ratio

            brush.texture_slot.scale = (1.0, 1.0, 1.0)
            brush.texture_slot.offset = (0.0, 0.0, 0.0)
            bpy.ops.brush.stencil_fit_image_aspect()
            
            scale_adj = bpy.context.scene.photogrammetry_properties.stencil_scale_adj
            scale_adj = (100.0 + scale_adj) / 100.0
            # Adjust stencil settings directly
            dims = (scale_adj*screen_width/2.0, scale_adj*screen_height/2.0)
            pos  = ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
            bpy.context.tool_settings.image_paint.brush.stencil_dimension = dims
            bpy.context.tool_settings.image_paint.brush.stencil_pos = pos
            # Ensure the offset sequence is correct # Prevent tiling
            brush.texture.extension = 'CLIP'
        else:
            # Create a new brush asset
            brush_asset = bpy.data.brushes.new(name="StencilBrush", mode='TEXTURE_PAINT')
            # Create a new texture
            texture = bpy.data.textures.new(name="StencilTexture", type='IMAGE')
            texture.image = reference_image
            # Assign the texture to the brush asset
            brush_asset.texture = texture
            # Add the brush asset to the asset library
            # (This step might not be necessary if you're directly using the brush)
            # bpy.ops.paint.brush_add_to_library(asset=brush_asset)
            # Set the new brush as the active brush
            bpy.context.tool_settings.image_paint.brush = brush_asset
            brush_asset.texture_slot.map_mode = 'STENCIL'
            brush = bpy.context.tool_settings.image_paint.brush

            # Adjust stencil image scale and offset to match screen dimensions while maintaining aspect ratio
            screen_aspect_ratio = screen_width / screen_height
            if reference_aspect_ratio > screen_aspect_ratio:
                scale_x = screen_width / reference_image.size[0]
                scale_y = scale_x / reference_aspect_ratio
            else:
                scale_y = screen_height / reference_image.size[1]
                scale_x = scale_y * reference_aspect_ratio

            brush.texture_slot.scale = (1.0, 1.0, 1.0)
            brush.texture_slot.offset = (0.0, 0.0, 0.0)
            bpy.ops.brush.stencil_fit_image_aspect()
            
            scale_adj = bpy.context.scene.photogrammetry_properties.stencil_scale_adj
            scale_adj = (100.0 + scale_adj) / 100.0
            # Adjust stencil settings directly
            dims = (scale_adj*screen_width/1.0, scale_adj*screen_height/1.0)
            pos  = ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
            bpy.context.tool_settings.image_paint.brush.stencil_dimension = dims
            bpy.context.tool_settings.image_paint.brush.stencil_pos = pos
            # Ensure the offset sequence is correct # Prevent tiling
            brush.texture.extension = 'CLIP'

#align_stencil_to_viewport()
#print("Stencil image aligned to match reference image dimensions in 3D viewport")

