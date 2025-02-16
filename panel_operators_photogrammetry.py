
import bpy
import os
import subprocess

from .utils_photogrammetry import *
from .utils_stencil import *

# Operator to call COLMAP
class WM_OT_CallColmap(bpy.types.Operator):
    bl_idname = "wm.call_colmap"
    bl_label = "Run COLMAP"

    def execute(self, context):
        tool_paths = context.scene.tool_paths
        colmap_path = tool_paths.colmap_path
        if not colmap_path:
            self.report({'WARNING'}, "COLMAP path is not set.")
            return {'CANCELLED'}

        call_colmap(colmap_path)

        self.report({'INFO'}, "COLMAP completed.")
        return {'FINISHED'}


# Operator to call COLMAP
class WM_OT_CreateRefImages(bpy.types.Operator):
    bl_idname = "wm.create_ref_images"
    bl_label = "Create Reference Images"

    def execute(self, context):
        
        delete_ref_images()
        populate_camera_poses()
        create_ref_images()

        return {'FINISHED'}




# Operator to call FFmpeg
class WM_OT_CallFfmpeg(bpy.types.Operator):
    bl_idname = "wm.call_ffmpeg"
    bl_label = "Extract video frames using FFmpeg"

    def execute(self, context):
        scene = context.scene.tool_paths
        ffmpeg_path = scene.ffmpeg_path
        video_path = bpy.path.abspath("//")
        start_time = scene.ffmpeg_start_time
        end_time = scene.ffmpeg_end_time
        frames_qty = scene.ffmpeg_frames
        seconds_qty = scene.ffmpeg_seconds
        
        if not ffmpeg_path:
            self.report({'WARNING'}, "FFmpeg path is not set.")
            return {'CANCELLED'}

        # Open file browser to select video file
        bpy.ops.wm.file_selector('INVOKE_DEFAULT')

        self.report({'INFO'}, "FFmpeg completed.")
        return {'FINISHED'}





class WM_OT_FileSelector(bpy.types.Operator):
    bl_idname = "wm.file_selector"
    bl_label = "Select Video File"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene.tool_paths
        ffmpeg_path = scene.ffmpeg_path
        video_path = bpy.path.abspath("//")
        start_time = scene.ffmpeg_start_time
        end_time = scene.ffmpeg_end_time
        frames_qty = scene.ffmpeg_frames
        seconds_qty = scene.ffmpeg_seconds
        scale_percentage = scene.ffmpeg_scale_percentage

        if not self.filepath:
            self.report({'WARNING'}, "No file selected.")
            return {'CANCELLED'}

        extract_frames_with_ffmpeg(self.filepath, ffmpeg_path, start_time, end_time, frames_qty, seconds_qty, scale_percentage )

        self.report({'INFO'}, "Frame extraction completed.")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}




# Operator to call COLMAP
class WM_OT_PlaceCamera(bpy.types.Operator):
    bl_idname = "wm.place_camera"
    bl_label = "Place camera to the selected photogrammetry image pose"

    def execute(self, context):

        set_camera_to_selected_image_pose()

        return {'FINISHED'}


# Operator to call COLMAP
class WM_OT_AlignStencil(bpy.types.Operator):
    bl_idname = "wm.align_stencil"
    bl_label = "Make brush stencil image match the reference image"

    def execute(self, context):

        align_stencil_to_viewport()

        return {'FINISHED'}




class WM_OT_IncrementImageIndex(bpy.types.Operator):
    bl_idname = "wm.increment_image_index"
    bl_label = "Make brush stencil image match the reference image"

    def execute(self, context):

        increment_image_index()

        return {'FINISHED'}



class WM_OT_DecrementImageIndex(bpy.types.Operator):
    bl_idname = "wm.decrement_image_index"
    bl_label = "Make brush stencil image match the reference image"

    def execute(self, context):

        decrement_image_index()

        return {'FINISHED'}




def register_photogrammetry():
    bpy.utils.register_class(WM_OT_CallColmap)
    bpy.utils.register_class(WM_OT_CreateRefImages)
    bpy.utils.register_class(WM_OT_CallFfmpeg)
    bpy.utils.register_class(WM_OT_FileSelector)
    bpy.utils.register_class(WM_OT_PlaceCamera)
    bpy.utils.register_class(WM_OT_AlignStencil)
    bpy.utils.register_class(WM_OT_IncrementImageIndex)
    bpy.utils.register_class(WM_OT_DecrementImageIndex)

def unregister_photogrammetry():
    bpy.utils.unregister_class(WM_OT_DecrementImageIndex)
    bpy.utils.unregister_class(WM_OT_IncrementImageIndex)
    bpy.utils.unregister_class(WM_OT_CreateRefImages)
    bpy.utils.unregister_class(WM_OT_CallColmap)
    bpy.utils.unregister_class(WM_OT_CallFfmpeg)
    bpy.utils.unregister_class(WM_OT_FileSelector)
    bpy.utils.unregister_class(WM_OT_PlaceCamera)
    bpy.utils.unregister_class(WM_OT_AlignStencil)

if __name__ == "__main__":
    register()




