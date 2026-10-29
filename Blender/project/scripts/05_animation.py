"""05: アニメーション ― キーフレームを打つ

【実行方法】  Ctrl+Shift+B
【結果】      "Sample_05" コレクションに、跳ねるボールと回転する立方体ができる
              Blender で スペースキー を押すと再生 (もう一度押すと停止)

【このサンプルで分かること】
    - obj.keyframe_insert() でキーフレームを打つ方法
    - フレーム範囲・フレームレートの設定
    - ループで計算した値をキーフレームにする方法 (サイン波など)
"""

import math

import bpy

from mylib.scene_utils import make_material, reset_collection

collection = reset_collection("Sample_05")
bpy.context.view_layer.active_layer_collection = (
    bpy.context.view_layer.layer_collection.children[collection.name])

# ---------------------------------------------------------------------------
# 0. シーンの設定: 120 フレーム (24fps なら 5 秒)
# ---------------------------------------------------------------------------
scene = bpy.context.scene
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 120


# ---------------------------------------------------------------------------
# 1. いちばん基本: 値を変えて keyframe_insert() を呼ぶ、の繰り返し
#    data_path には "location" / "rotation_euler" / "scale" などを指定する
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_cube_add(size=1.0)
cube = bpy.context.active_object
cube.name = "S05_Spinner"
cube.data.materials.append(make_material("S05_Orange", (1.0, 0.4, 0.05)))

cube.location = (0.0, 0.0, 0.5)
cube.rotation_euler = (0.0, 0.0, 0.0)
cube.keyframe_insert(data_path="rotation_euler", frame=1)    # 1 フレーム目: 0 度

cube.rotation_euler = (0.0, 0.0, math.radians(360))
cube.keyframe_insert(data_path="rotation_euler", frame=120)  # 120 フレーム目: 1 回転

# index を指定すると 1 成分だけ (0=X, 1=Y, 2=Z) にキーを打てる
cube.location.x = -3.0
cube.keyframe_insert(data_path="location", index=0, frame=1)
cube.location.x = 3.0
cube.keyframe_insert(data_path="location", index=0, frame=60)
cube.location.x = -3.0
cube.keyframe_insert(data_path="location", index=0, frame=120)


# ---------------------------------------------------------------------------
# 2. 計算でキーフレームを打つ: 跳ねるボール
#    |sin| の形で上下させ、毎フレームにキーを打つ
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4)
ball = bpy.context.active_object
ball.name = "S05_Ball"
ball.data.materials.append(make_material("S05_Red", (0.9, 0.1, 0.1)))
for poly in ball.data.polygons:
    poly.use_smooth = True

bounces = 4      # 120 フレームで 4 回跳ねる
height = 2.5
for frame in range(1, 121):
    t = (frame - 1) / 119                     # 0.0 → 1.0
    z = abs(math.sin(t * math.pi * bounces))  # 0〜1 を行ったり来たり
    ball.location = (t * 6.0 - 3.0, 2.0, 0.4 + z * height * (1.0 - t * 0.6))  # だんだん低く
    ball.keyframe_insert(data_path="location", frame=frame)


# ---------------------------------------------------------------------------
# 3. 拡大縮小 (scale) で「鼓動」
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.5, location=(0.0, -2.5, 0.6))
heart = bpy.context.active_object
heart.name = "S05_Pulse"
heart.data.materials.append(make_material("S05_Pink", (1.0, 0.3, 0.6)))

for frame in range(1, 121, 10):  # 10 フレームごと
    s = 1.0 if (frame // 10) % 2 == 0 else 1.4  # 交互に 1.0 倍 / 1.4 倍
    heart.scale = (s, s, s)
    heart.keyframe_insert(data_path="scale", frame=frame)


# 現在フレームを 1 に戻し、結果を表示
scene.frame_set(1)
print(f"フレーム {scene.frame_start}〜{scene.frame_end} にキーフレームを作成しました")
print("Blender でスペースキーを押すと再生できます")
