
import bpy
import os
import math
import subprocess
import numpy as np
from mathutils import Matrix, Quaternion, Vector


def extract_frames_with_ffmpeg(video_path, ffmpeg_path, start_time, end_time, frames_qty, seconds_qty, scale_percentage=20.0 ):
    # Get the directory of the current Blender file
    blender_file_dir = os.path.dirname(bpy.data.filepath)
    
    # Define the images directory path
    images_path = os.path.join(blender_file_dir, 'images')

    # Create the images directory if it doesn't exist
    os.makedirs(images_path, exist_ok=True)

    # Ensure FFmpeg path is valid
    if not os.path.isfile(ffmpeg_path):
        print(f"Invalid FFmpeg path: {ffmpeg_path}")
        return

    # Get the video duration
    result = subprocess.run([ffmpeg_path, "-i", video_path], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    duration_str = [x for x in result.stderr.split('\n') if "Duration" in x]
    duration_str = duration_str[0].split()[1].split(",")[0]
    hours, minutes, seconds = map(float, duration_str.split(":"))
    video_duration = hours * 3600 + minutes * 60 + seconds

    # Adjust start time and end time
    start_time = max(0, start_time)
    if end_time < 0 or end_time > video_duration:
        end_time = video_duration

    # Calculate FPS
    fps = frames_qty / seconds_qty

    # Calculate scale factor
    scale_factor = scale_percentage / 100

    # FFmpeg command to extract and scale frames
    ffmpeg_command = [
        ffmpeg_path,
        '-i', video_path,
        '-vf', f"fps={fps},scale=iw*{scale_factor}:ih*{scale_factor},trim=start={start_time}:end={end_time}",
        os.path.join(images_path, 'frame_%04d.png')
    ]

    # Run FFmpeg command
    subprocess.run(ffmpeg_command)

    print( "Done" )






def call_colmap(colmap_path):
    # Get the directory of the current Blender file
    blender_file_dir = os.path.dirname(bpy.data.filepath)
    
    # Define paths
    image_path = os.path.join(blender_file_dir, 'images')
    colmap_folder = os.path.join(blender_file_dir, 'colmap')
    photogrammetry_folder = os.path.join(blender_file_dir, 'photogrammetry')

    # Create directories if they don't exist
    os.makedirs(colmap_folder, exist_ok=True)
    os.makedirs(photogrammetry_folder, exist_ok=True)

    # Define database path
    database_path = os.path.join(colmap_folder, 'database.db')

    # Ensure COLMAP path is valid
    if not os.path.isfile(colmap_path):
        print(f"Invalid COLMAP path: {colmap_path}")
        return
    
    #print( "Creating the database" )

    # Call COLMAP commands using the subprocess module
    print( "Extracting features" )
    subprocess.run([colmap_path, "feature_extractor", 
                    "--database_path", database_path,
                    "--image_path", image_path, 
                    '--ImageReader.camera_model', 'PINHOLE', 
                    '--ImageReader.single_camera', '1']) 

    print( "Running matcher" )
    subprocess.run([colmap_path, "exhaustive_matcher",
                    "--database_path", database_path])

    print( "Running mapper" )
    subprocess.run([colmap_path, "mapper",
                    "--database_path", database_path,
                    "--image_path", image_path,
                    "--output_path", colmap_folder])

    print( "Saving the results" )
    subprocess.run([colmap_path, "model_converter",
                    "--input_path", os.path.join(colmap_folder, "0"),
                    "--output_path", photogrammetry_folder,
                    "--output_type", "TXT"])

    print( "Done" )



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



def convert_colmap_to_blender(rx, ry, rz, qw, qx, qy, qz):
    # COLMAP to Blender translation
    location = Vector((rx, ry, rz))

    # COLMAP to Blender rotation
    #colmap_quat = Quaternion((qw, qx, qy, qz))
    t = Quaternion((qw, qx, qy, qz)).to_matrix().to_4x4()
    t.translation = location * 5
    # Swap axes for Blender
    t0 = Quaternion((1, 0, 0), 3.14159 / 2).to_matrix().to_4x4()
    t = t0 @ t

    print( "transform: ", t )

    return t


def _read_images_file(filepath):
    image_poses = {}

    # Read the file and skip lines starting with #
    with open(filepath, 'r') as file:
        lines = [line for line in file if not line.startswith('#') and line.strip()]

    # Process the remaining lines in pairs
    for i in range(0, len(lines), 2):
        line = lines[i]
        parts = line.split()
        image_id = parts[0]
        qw, qx, qy, qz = map(float, parts[1:5])
        tx, ty, tz = map(float, parts[5:8])
        t = convert_colmap_to_blender(tx, ty, tz, qw, qx, qy, qz)
        camera_id = parts[8]
        image_name = parts[9]
        transform_matrix = t
        
        # Apply the conversion to Blender's reference frame
        #transform_matrix = rot_180_x @ colmap_to_blender @ transform_matrix @ colmap_to_blender.inverted()
        
        image_poses[image_name] = {
            'transform': transform_matrix,
            'camera_id': camera_id
        }

    return image_poses




def _read_cameras_file(filepath):
    camera_intrinsics = {}
    with open(filepath, 'r') as file:
        lines = file.readlines()

    for line in lines:
        if line.startswith('#') or not line.strip():
            continue
        parts = line.split()
        camera_id = parts[0]
        model = parts[1]
        width = int(parts[2])
        height = int(parts[3])
        params = list(map(float, parts[4:]))
        camera_intrinsics[camera_id] = {
            'model': model,
            'width': width,
            'height': height,
            'params': params
        }
    return camera_intrinsics






def populate_camera_poses():
    # Define paths
    blender_file_dir = os.path.dirname(bpy.data.filepath)
    images_file_path = os.path.join(blender_file_dir, 'photogrammetry', 'images.txt')
    cameras_file_path = os.path.join(blender_file_dir, 'photogrammetry', 'cameras.txt')

    # Read image poses and camera intrinsics
    image_poses = _read_images_file(images_file_path)
    camera_intrinsics = _read_cameras_file(cameras_file_path)

    # Create property groups
    bpy.context.scene.image_pose_properties.clear()
    for image_name, pose in image_poses.items():
        item = bpy.context.scene.image_pose_properties.add()
        item.image_path = os.path.join(blender_file_dir, 'images', image_name)
        item.transform = [elem for row in pose['transform'] for elem in row]
        
        # Assuming the same camera intrinsics for all images for simplicity
        camera_id = list(camera_intrinsics.keys())[0]
        intrinsics = camera_intrinsics[camera_id]
        params = intrinsics['params']
        if intrinsics['model'] == 'SIMPLE_PINHOLE':
            item.fx = item.fy = params[0]
            item.cx = params[1]
            item.cy = params[2]
        elif intrinsics['model'] == 'PINHOLE':
            item.fx = params[0]
            item.fy = params[1]
            item.cx = params[2]
            item.cy = params[3]


# Function to apply camera intrinsics and pose to the viewport
def apply_camera_settings(camera_props):
    # Get the Blender camera
    camera = bpy.data.objects['Camera']
    
    # Set camera intrinsics
    fx = camera_props.fx
    fy = camera_props.fy
    cx = camera_props.cx
    cy = camera_props.cy
    width = bpy.context.scene.render.resolution_x
    height = bpy.context.scene.render.resolution_y

    camera.data.lens = fx * (camera.data.sensor_width / width)
    camera.data.shift_x = (width / 2 - cx) / width
    camera.data.shift_y = (cy - height / 2) / height

    # Set camera pose
    transform_matrix = Matrix(camera_props.transform) #.transposed()
    camera.matrix_world = transform_matrix

    # Set the viewport to camera view
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.region_3d.view_perspective = 'CAMERA'


def _create_image_object(camera_props, offset_distance=1.0):
    # Load the image
    image_path = camera_props.image_path
    image_name = os.path.basename(image_path)
    image = bpy.data.images.load(image_path)

    # Create a reference image object
    #bpy.ops.object.empty_add(type='IMAGE', radius=1)
    bpy.ops.object.load_reference_image(filepath=image_path)

    ref_image = bpy.context.object
    ref_image.name = f"RefImage_{image_name}"
    #ref_image.data = image
    #ref_image.empty_image_offset = (0.5, 0.5)
    #ref_image.empty_image_depth = 'DEFAULT'
    
    # Get the aspect ratio of the image
    aspect_ratio = image.size[0] / image.size[1]
    ref_image.scale = (aspect_ratio, 1, 1)

    # Set the reference image's transformation matrix
    transform_matrix = Matrix(camera_props.transform).transposed()

    # Offset the reference image slightly in front of the camera
    #offset_vector = transform_matrix.to_3x3().inverted() @ Vector((0, 0, -offset_distance))
    #transform_matrix.translation += offset_vector

    ref_image.matrix_world = transform_matrix
    # Make the image non-selectable
    ref_image.hide_select = True


def create_ref_images( offset_distance=1.0 ):
    props = bpy.context.scene.image_pose_properties
    for prop in props:
        _create_image_object( prop, offset_distance )


