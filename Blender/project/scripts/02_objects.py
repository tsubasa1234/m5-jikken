"""02: オブジェクト ― 作る・動かす・回す・拡大する・消す

【実行方法】  Ctrl+Shift+B
【結果】      "Sample_02" コレクションに立方体・球・円柱・自作の三角錐が並ぶ

【このサンプルで分かること】
    - bpy.ops でプリミティブ (立方体など) を追加する方法
    - 位置 location / 回転 rotation_euler / 拡大 scale の変え方
    - bpy.data だけでメッシュを一から作る方法 (頂点と面を自分で指定)
    - 何度実行しても同じ結果になるよう、前回の結果を消してから作る書き方
"""

import math  # 角度の変換 (math.radians) に使う

import bpy

COLLECTION_NAME = "Sample_02"

# ---------------------------------------------------------------------------
# 0. 準備: 前回の実行結果を消す
#    これをしないと Ctrl+Shift+B を押すたびにオブジェクトが増えていく。
#    (03 以降はこの処理を mylib.scene_utils.reset_collection() にまとめて使う)
# ---------------------------------------------------------------------------
collection = bpy.data.collections.get(COLLECTION_NAME)
if collection is None:
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)  # シーンに追加
else:
    for obj in list(collection.objects):  # list() でコピーしてからループ (削除中に変わるため)
        bpy.data.objects.remove(obj, do_unlink=True)

# 以降 bpy.ops で追加したオブジェクトがこのコレクションに入るよう、アクティブにしておく
layer_collection = bpy.context.view_layer.layer_collection.children[COLLECTION_NAME]
bpy.context.view_layer.active_layer_collection = layer_collection


# ---------------------------------------------------------------------------
# 1. bpy.ops でプリミティブを追加する
#    「追加 → メッシュ → 立方体」と同じ操作。追加されたものがアクティブになるので
#    bpy.context.active_object で受け取る
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.5))
cube = bpy.context.active_object
cube.name = "S02_Cube"

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(2.0, 0.0, 0.5))
sphere = bpy.context.active_object
sphere.name = "S02_Sphere"

bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=1.0, location=(4.0, 0.0, 0.5))
cylinder = bpy.context.active_object
cylinder.name = "S02_Cylinder"


# ---------------------------------------------------------------------------
# 2. 位置・回転・拡大を変える
# ---------------------------------------------------------------------------
# 位置: タプルでまとめて代入、または .x .y .z で個別に
cube.location = (0.0, 0.0, 0.5)
cube.location.y += 1.0  # Y 方向に 1 だけ動かす

# 回転: 単位は「ラジアン」。度で考えたいときは math.radians() で変換する
cube.rotation_euler = (0.0, 0.0, math.radians(45))  # Z 軸まわりに 45 度

# 拡大: 1.0 が等倍。(X, Y, Z) の倍率
cylinder.scale = (1.0, 1.0, 2.0)  # 縦に 2 倍
cylinder.location.z = 1.0  # 縦に伸びたぶん持ち上げる

# 見た目を滑らかにする (右クリック → スムーズシェード と同じ)
for poly in sphere.data.polygons:
    poly.use_smooth = True


# ---------------------------------------------------------------------------
# 3. bpy.data だけでメッシュを作る (bpy.ops を使わない方法)
#    頂点 (vertices) と、どの頂点で面を張るか (faces) を自分で指定する。
#    bpy.ops より速く、状況 (選択状態など) に左右されないので大量生成に向く。
# ---------------------------------------------------------------------------
vertices = [
    (-0.5, -0.5, 0.0),  # 0: 底面の四隅
    (0.5, -0.5, 0.0),   # 1
    (0.5, 0.5, 0.0),    # 2
    (-0.5, 0.5, 0.0),   # 3
    (0.0, 0.0, 1.2),    # 4: てっぺん
]
faces = [
    (0, 3, 2, 1),  # 底面 (外から見て時計回り → 法線が下向き)
    (0, 1, 4),     # 側面 ×4 (外から見て反時計回り → 法線が外向き)
    (1, 2, 4),
    (2, 3, 4),
    (3, 0, 4),
]
mesh = bpy.data.meshes.new("S02_PyramidMesh")  # メッシュ (形のデータ)
mesh.from_pydata(vertices, [], faces)          # 頂点・辺・面 (辺は自動なので空)
mesh.update()

pyramid = bpy.data.objects.new("S02_Pyramid", mesh)  # オブジェクト (位置などを持つ入れ物)
pyramid.location = (6.0, 0.0, 0.0)
collection.objects.link(pyramid)  # bpy.data で作ったものは自分でコレクションに入れる


# ---------------------------------------------------------------------------
# 4. ループでたくさん作る
# ---------------------------------------------------------------------------
for i in range(8):
    angle = math.radians(i * 45)  # 0, 45, 90, ... 度
    x = 3.0 + 2.5 * math.cos(angle)
    y = -4.0 + 2.5 * math.sin(angle)
    bpy.ops.mesh.primitive_cube_add(size=0.4, location=(x, y, 0.2))
    small = bpy.context.active_object
    small.name = f"S02_Ring_{i}"
    small.rotation_euler.z = angle  # 円の外側を向かせる


# ---------------------------------------------------------------------------
# 5. 削除
#    bpy.data.objects.remove() で消せる。例として 1 個作って消してみる
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_monkey_add(location=(0.0, -4.0, 0.5))
temp = bpy.context.active_object
print("一時的に作成:", temp.name)
bpy.data.objects.remove(temp, do_unlink=True)
print("削除しました")

print(f"{COLLECTION_NAME} に {len(collection.objects)} 個のオブジェクトを作成しました")
