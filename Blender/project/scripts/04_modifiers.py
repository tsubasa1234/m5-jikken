"""04: モディファイア ― 形を壊さずに加工する

【実行方法】  Ctrl+Shift+B
【結果】      "Sample_04" コレクションに、モディファイアをかけたオブジェクトが並ぶ
              プロパティパネルのスパナ (🔧) タブで、追加されたモディファイアを確認・調整できる

【このサンプルで分かること】
    - obj.modifiers.new(名前, 種類) でモディファイアを追加する方法
    - よく使うモディファイア: サブディビジョン / ベベル / 配列 / ミラー / ソリッド化
    - 設定値の変え方
"""

import bpy

from mylib.scene_utils import make_material, reset_collection

collection = reset_collection("Sample_04")
bpy.context.view_layer.active_layer_collection = (
    bpy.context.view_layer.layer_collection.children[collection.name])

blue = make_material("S04_Blue", (0.2, 0.4, 0.9), roughness=0.3)


def add_cube(name, x, size=1.0):
    bpy.ops.mesh.primitive_cube_add(size=size, location=(x, 0.0, size / 2))
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(blue)
    return obj


# ---------------------------------------------------------------------------
# 1. サブディビジョンサーフェス: 角を丸めて滑らかにする
#    modifiers.new("表示名", type="種類")
#    種類の文字列は公式ドキュメント bpy.types.Modifier の type を参照
# ---------------------------------------------------------------------------
smooth = add_cube("S04_Subdivision", 0.0)
mod = smooth.modifiers.new("Subdivision", type="SUBSURF")
mod.levels = 2          # ビューポートでの分割数
mod.render_levels = 3   # レンダリング時の分割数
for poly in smooth.data.polygons:
    poly.use_smooth = True


# ---------------------------------------------------------------------------
# 2. ベベル: 角を面取りする
# ---------------------------------------------------------------------------
bevel_cube = add_cube("S04_Bevel", 2.0)
bevel = bevel_cube.modifiers.new("Bevel", type="BEVEL")
bevel.width = 0.1     # 面取りの幅
bevel.segments = 4    # 丸みの細かさ (1 だと平らな面取り)


# ---------------------------------------------------------------------------
# 3. 配列: 同じ形を並べて複製する
# ---------------------------------------------------------------------------
stairs = add_cube("S04_Array", 4.0, size=0.5)
array = stairs.modifiers.new("Array", type="ARRAY")
array.count = 6
array.relative_offset_displace = (1.0, 0.0, 1.0)  # 1 個ずつ X と Z にずらす → 階段


# ---------------------------------------------------------------------------
# 4. ミラー: 片側だけ作って反対側を自動で作る
#    わざと X 方向にずらした立方体をミラーすると左右対称に 2 つ並ぶ
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(9.0, 0.0, 0.25))
mirrored = bpy.context.active_object
mirrored.name = "S04_Mirror"
mirrored.data.materials.append(blue)
# メッシュの頂点だけを +X 側へ 0.6 ずらす (オブジェクトの原点は x=9 のまま)
for v in mirrored.data.vertices:
    v.co.x += 0.6
mirror = mirrored.modifiers.new("Mirror", type="MIRROR")
mirror.use_axis = (True, False, False)  # X 軸で反転


# ---------------------------------------------------------------------------
# 5. 複数のモディファイアを重ねる (上から順に適用される)
#    平面 → ソリッド化で厚みをつける → ベベルで角を丸める
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=1.5, location=(12.0, 0.0, 0.1))
plate = bpy.context.active_object
plate.name = "S04_Stack"
plate.data.materials.append(blue)

solid = plate.modifiers.new("Solidify", type="SOLIDIFY")
solid.thickness = 0.2
plate_bevel = plate.modifiers.new("Bevel", type="BEVEL")
plate_bevel.width = 0.05
plate_bevel.segments = 3

print("S04_Stack のモディファイア (適用順):", [m.name for m in plate.modifiers])


# ---------------------------------------------------------------------------
# ヒント: モディファイアを「適用」してメッシュに確定させたいとき
#   with bpy.context.temp_override(object=obj, active_object=obj):
#       bpy.ops.object.modifier_apply(modifier="Bevel")
#   VSCode からの実行では画面の情報 (context) が限られるので、
#   context が必要な bpy.ops は temp_override で対象を指定すると確実
# ---------------------------------------------------------------------------
