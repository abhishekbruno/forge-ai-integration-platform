"""Trusted Blender Python runner script.

Executed strictly inside Blender's embedded Python interpreter:
`blender --background [scene.blend] --python-exit-code 1 --python blender_runner.py -- <request-json> <result-json>`

Never imported directly by the host FORGE environment.
"""

from __future__ import annotations

import json
import os
import sys

# Attempt importing bpy within Blender's runtime
try:
    import bpy
except ImportError:
    bpy = None  # Will fail gracefully if run outside Blender


def fail(error_message: str, code: int = 1) -> None:
    result = {"success": False, "error": error_message}
    if len(sys.argv) > 2:
        res_file = sys.argv[-1]
        try:
            with open(res_file, "w", encoding="utf-8") as f:
                json.dump(result, f)
        except Exception:
            pass
    print(f"FORGE_BLENDER_ERROR: {error_message}", file=sys.stderr)
    sys.exit(code)


def handle_scene_summary(args: dict) -> dict:
    objects = bpy.data.objects
    types_count: dict[str, int] = {}
    for obj in objects:
        types_count[obj.type] = types_count.get(obj.type, 0) + 1

    cameras = [cam.name for cam in bpy.data.cameras]
    lights = [light.name for light in bpy.data.lights]
    collections = [col.name for col in bpy.data.collections]

    return {
        "object_count": len(objects),
        "object_types": types_count,
        "cameras": cameras[:50],
        "lights": lights[:50],
        "collections": collections[:50],
        "blender_version": ".".join(str(v) for v in bpy.app.version),
    }


def handle_list_objects(args: dict) -> dict:
    limit = min(int(args.get("limit", 50)), 200)
    objs = []
    for obj in list(bpy.data.objects)[:limit]:
        loc = [round(float(v), 4) for v in obj.location]
        rot = [round(float(v), 4) for v in obj.rotation_euler]
        scale = [round(float(v), 4) for v in obj.scale]
        objs.append(
            {
                "name": obj.name,
                "type": obj.type,
                "location": loc,
                "rotation_euler": rot,
                "scale": scale,
            }
        )
    return {
        "objects": objs,
        "total": len(bpy.data.objects),
    }


def handle_inspect_object(args: dict) -> dict:
    name = str(args.get("object_name", "")).strip()
    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found in scene.")

    loc = [round(float(v), 4) for v in obj.location]
    rot = [round(float(v), 4) for v in obj.rotation_euler]
    scale = [round(float(v), 4) for v in obj.scale]
    dims = [round(float(v), 4) for v in obj.dimensions]
    materials = [slot.material.name for slot in obj.material_slots if slot.material]
    parent = obj.parent.name if obj.parent else None

    return {
        "name": obj.name,
        "type": obj.type,
        "location": loc,
        "rotation_euler": rot,
        "scale": scale,
        "dimensions": dims,
        "materials": materials,
        "parent": parent,
    }


def handle_list_materials(args: dict) -> dict:
    mats = []
    for mat in list(bpy.data.materials)[:100]:
        mats.append(
            {
                "name": mat.name,
                "use_nodes": getattr(mat, "use_nodes", False),
                "user_count": getattr(mat, "users", 0),
            }
        )
    return {
        "materials": mats,
        "total": len(bpy.data.materials),
    }


def handle_create_primitive(args: dict) -> dict:
    prim_type = args.get("primitive_type", "cube").lower()
    name = args.get("name", "Primitive")
    loc = tuple(args.get("location", [0.0, 0.0, 0.0]))
    size = float(args.get("size", 2.0))
    output_file = args.get("output_file")

    if not output_file:
        raise ValueError("output_file is required for mutating primitive creation.")

    if prim_type == "cube":
        bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    elif prim_type == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=size / 2.0, location=loc)
    elif prim_type == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(radius=size / 2.0, depth=size, location=loc)
    elif prim_type == "plane":
        bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    else:
        raise ValueError(f"Unsupported primitive type: '{prim_type}'")

    created_obj = bpy.context.active_object
    if created_obj:
        created_obj.name = name

    # Save to NEW output file
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(output_file))

    return {
        "success": True,
        "created_name": name,
        "output_file": output_file,
        "source_preserved": True,
    }


def handle_set_transform(args: dict) -> dict:
    name = str(args.get("object_name", "")).strip()
    output_file = args.get("output_file")
    if not output_file:
        raise ValueError("output_file required for set_transform.")

    obj = bpy.data.objects.get(name)
    if not obj:
        raise ValueError(f"Object '{name}' not found for transform update.")

    if "location" in args and args["location"]:
        obj.location = tuple(args["location"])
    if "rotation_euler" in args and args["rotation_euler"]:
        obj.rotation_euler = tuple(args["rotation_euler"])
    if "scale" in args and args["scale"]:
        obj.scale = tuple(args["scale"])

    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(output_file))
    return {
        "success": True,
        "object_name": name,
        "output_file": output_file,
    }


def handle_rename_object(args: dict) -> dict:
    old_name = str(args.get("old_name", "")).strip()
    new_name = str(args.get("new_name", "")).strip()
    output_file = args.get("output_file")
    if not output_file:
        raise ValueError("output_file required for rename_object.")

    obj = bpy.data.objects.get(old_name)
    if not obj:
        raise ValueError(f"Object '{old_name}' not found for renaming.")

    obj.name = new_name
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(output_file))
    return {
        "success": True,
        "renamed_from": old_name,
        "renamed_to": obj.name,
        "output_file": output_file,
    }


def handle_save_scene_copy(args: dict) -> dict:
    output_file = args.get("output_file")
    if not output_file:
        raise ValueError("output_file required for save_scene_copy.")

    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(output_file))
    return {
        "success": True,
        "output_file": output_file,
    }


DISPATCH_TABLE = {
    "blender.scene_summary": handle_scene_summary,
    "blender.list_objects": handle_list_objects,
    "blender.inspect_object": handle_inspect_object,
    "blender.list_materials": handle_list_materials,
    "blender.create_primitive": handle_create_primitive,
    "blender.set_transform": handle_set_transform,
    "blender.rename_object": handle_rename_object,
    "blender.save_scene_copy": handle_save_scene_copy,
}


def main() -> None:
    if not bpy:
        fail("This script must be executed by Blender's python interpreter.", 2)

    # Args passed after '--'
    try:
        sep_index = sys.argv.index("--")
        custom_args = sys.argv[sep_index + 1 :]
    except ValueError:
        fail("Missing '--' separator for runner arguments.")

    if len(custom_args) < 2:
        fail("Expected <request.json> and <result.json> paths.")

    req_file = custom_args[0]
    res_file = custom_args[1]

    if not os.path.isfile(req_file):
        fail(f"Request file does not exist: {req_file}")

    try:
        with open(req_file, "r", encoding="utf-8") as f:
            request_data = json.load(f)
    except Exception as exc:
        fail(f"Failed to parse request JSON: {exc}")

    handler = request_data.get("handler")
    args = request_data.get("args", {})

    if handler not in DISPATCH_TABLE:
        fail(f"Unrecognized Blender handler: '{handler}'")

    try:
        result_payload = DISPATCH_TABLE[handler](args)
        final_result = {
            "success": True,
            "data": result_payload,
        }
        with open(res_file, "w", encoding="utf-8") as f:
            json.dump(final_result, f, indent=2)
        sys.exit(0)
    except Exception as exc:
        fail(f"Handler execution failure: {exc}")


if __name__ == "__main__":
    main()
