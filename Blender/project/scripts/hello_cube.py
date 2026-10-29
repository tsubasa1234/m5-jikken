"""動作確認用スクリプト: VSCode でこのファイルを開いて Ctrl+Shift+B"""

import bpy

from mylib.shapes import add_cube

print("Blender", bpy.app.version_string, "から実行中")

# 前回の実行で作ったキューブを消してから作り直す
for obj in [o for o in bpy.data.objects if o.name.startswith("VSCodeCube")]:
    bpy.data.objects.remove(obj, do_unlink=True)

for i in range(3):
    cube = add_cube(f"VSCodeCube_{i}", location=(i * 2.5, 0.0, 0.0))
    print("作成:", cube.name)
