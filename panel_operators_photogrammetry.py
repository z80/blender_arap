
import bpy
import os
import subprocess

from utils_photogrammetry import *

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

        if not self.filepath:
            self.report({'WARNING'}, "No file selected.")
            return {'CANCELLED'}

        extract_frames_with_ffmpeg(self.filepath, ffmpeg_path, start_time, end_time, frames_qty, seconds_qty)

        self.report({'INFO'}, "Frame extraction completed.")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}






# Define the property group
class ImagePoseProperties(bpy.types.PropertyGroup):
    image_path: bpy.props.StringProperty(
        name="Image Path",
        description="Path to the image",
        default="",
        subtype='FILE_PATH'
    )
    transform: bpy.props.FloatVectorProperty(
        name="Transform",
        size=16,
        subtype='MATRIX',
        default=[1.0, 0.0, 0.0, 0.0,  # 4x4 identity matrix
                 0.0, 1.0, 0.0, 0.0,
                 0.0, 0.0, 1.0, 0.0,
                 0.0, 0.0, 0.0, 1.0]
    )
    fx: bpy.props.FloatProperty(name="fx")
    fy: bpy.props.FloatProperty(name="fy")
    cx: bpy.props.FloatProperty(name="cx")
    cy: bpy.props.FloatProperty(name="cy")











def register_photogrammetry():
    bpy.utils.register_class(WM_OT_CallColmap)
    bpy.utils.register_class(WM_OT_CreateRefImages)
    bpy.utils.register_class(WM_OT_CallFfmpeg)
    bpy.utils.register_class(WM_OT_FileSelector)
    bpy.utils.register_class(ImagePoseProperties)
    bpy.types.Scene.photogrammetry_properties = bpy.props.PointerProperty(type=PhotogrammetryProperties)

def unregister_photogrammetry():
    bpy.utils.unregister_class(WM_OT_CreateRefImages)
    bpy.utils.unregister_class(WM_OT_CallColmap)
    bpy.utils.unregister_class(WM_OT_CallFfmpeg)
    bpy.utils.unregister_class(WM_OT_FileSelector)
    bpy.utils.unregister_class(ImagePoseProperties)
    del bpy.types.Scene.image_pose_properties

if __name__ == "__main__":
    register()




