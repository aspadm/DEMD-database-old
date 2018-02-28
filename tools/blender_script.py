import os
import bpy
import sys

# Names of folder and files
args = sys.argv

source_file = args[-2]
convert_file = args[-1]
save_type = convert_file.split(".")[-1]

# Deleting all objects
for scene in bpy.data.scenes:
    for obj in scene.objects:
        scene.objects.unlink(obj)
for bpy_data_iter in (
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.lamps,
        bpy.data.cameras,
        ):
    for id_data in bpy_data_iter:
        bpy_data_iter.remove(id_data)
bpy.ops.object.select_by_type(type = "MESH")
bpy.ops.object.delete(use_global=False)
for item in bpy.data.meshes:   
    for scene in bpy.data.scenes:
        for obj in scene.objects:
            scene.objects.unlink(obj) 
    item.user_clear()
    bpy.data.meshes.remove(item)
print("Scene cleared")

# Open model and save
try:
    try:
        print("Try to use plugin...")
        bpy.ops.import_scene.deusexmd(filepath=source_file)
        print("Success")
    except:
        try:
            print("Fail")
            print("Try to use outer script...")
            try:
                import import_DeusExMD
            except:
                print("Fail to import")
                exit(2)
            print("Successful module import; try to open model...")
            import_DeusExMD.import_DeusExMD(source_file, #filepath
                                        bpy.context, #context
                                        False, #randomize_colors
                                        True, #import_vertcolors
                                        False, #skip_blank
                                        False, #use_layers
                                        1.0) #mesh_scale
            print("Success")
        except:
            print("Fail")
            exit(1)

    print("\nModel opened\n")
    if save_type == "obj":
        bpy.ops.export_scene.obj(filepath=convert_file)
    elif save_type == "fbx":
        bpy.ops.export_scene.fbx(filepath=convert_file)
    elif save_type == "3ds":
        bpy.ops.export_scene.autodesk_3ds(filepath=convert_file)
    elif save_type == "stl":
        bpy.ops.export_mesh.stl(filepath=convert_file,
                                 check_existing=False,
                                 ascii=False)
    else:
        print("Incorrect save format")
    print("\nConvertions done!")
    exit(0)

# In case of error
except Exception:
    print("\nSome errors here")
    exit(1)
