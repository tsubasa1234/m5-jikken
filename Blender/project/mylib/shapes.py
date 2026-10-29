"""動作確認用: プロジェクトルート基準で import されるモジュール"""

import bpy


def add_cube(name, location=(0.0, 0.0, 0.0), size=1.0):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj
