"""03: マテリアル ― 色・金属・ガラスをつける

【実行方法】  Ctrl+Shift+B
【結果】      "Sample_03" コレクションに色違いの球が並ぶ
              色を見るには 3D ビュー右上のシェーディングを「マテリアルプレビュー」(Z キー → 2) にする

【このサンプルで分かること】
    - マテリアルを作ってオブジェクトに割り当てる方法
    - Principled BSDF ノードの入力 (Base Color / Metallic / Roughness など) の変え方
    - 自作モジュール mylib の関数を import して使う方法
"""

import bpy

# mylib/scene_utils.py の関数を使う。
# send_to_blender.py がプロジェクトルート (project/) を sys.path に追加するので import できる
from mylib.scene_utils import make_material, reset_collection

collection = reset_collection("Sample_03")  # 前回の結果を消して空のコレクションを用意

# 追加したオブジェクトがこのコレクションに入るようにする
bpy.context.view_layer.active_layer_collection = (
    bpy.context.view_layer.layer_collection.children[collection.name])


def add_sphere(name, x):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(x, 0.0, 0.8))
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()  # アクティブオブジェクトをスムーズシェードに
    return obj


# ---------------------------------------------------------------------------
# 1. 基本: マテリアルを作って割り当てる (関数を使わずに全部書いた版)
# ---------------------------------------------------------------------------
red_sphere = add_sphere("S03_Red", 0.0)

mat = bpy.data.materials.get("S03_Red") or bpy.data.materials.new("S03_Red")
# Blender 5.0 以降、マテリアルは常にノードで作られる (以前の mat.use_nodes = True は不要)
# 新しいマテリアルには最初から "Principled BSDF" ノードが入っている
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.8, 0.05, 0.05, 1.0)  # (R, G, B, A) 0〜1
bsdf.inputs["Roughness"].default_value = 0.4  # 0 = ツルツル, 1 = ザラザラ

# オブジェクトに割り当てる (マテリアルスロットに追加)
red_sphere.data.materials.clear()
red_sphere.data.materials.append(mat)


# ---------------------------------------------------------------------------
# 2. 関数 make_material() を使うと 1 行で済む
# ---------------------------------------------------------------------------
gold = add_sphere("S03_Gold", 2.0)
gold.data.materials.append(make_material("S03_Gold", (1.0, 0.75, 0.2), metallic=1.0, roughness=0.2))

rubber = add_sphere("S03_Rubber", 4.0)
rubber.data.materials.append(make_material("S03_Rubber", (0.05, 0.05, 0.05), roughness=0.9))


# ---------------------------------------------------------------------------
# 3. ガラス: 透過 (Transmission) を 1 にする
# ---------------------------------------------------------------------------
glass = add_sphere("S03_Glass", 6.0)
glass_mat = make_material("S03_Glass", (0.9, 0.95, 1.0), roughness=0.0)
glass_bsdf = glass_mat.node_tree.nodes["Principled BSDF"]
glass_bsdf.inputs["Transmission Weight"].default_value = 1.0
glass_bsdf.inputs["IOR"].default_value = 1.45  # 屈折率 (ガラスは 1.45 前後)
glass.data.materials.append(glass_mat)


# ---------------------------------------------------------------------------
# 4. 発光 (Emission)
# ---------------------------------------------------------------------------
lamp = add_sphere("S03_Emission", 8.0)
lamp_mat = make_material("S03_Emission", (0.2, 0.6, 1.0))
lamp_bsdf = lamp_mat.node_tree.nodes["Principled BSDF"]
lamp_bsdf.inputs["Emission Color"].default_value = (0.2, 0.6, 1.0, 1.0)
lamp_bsdf.inputs["Emission Strength"].default_value = 5.0
lamp.data.materials.append(lamp_mat)


# ---------------------------------------------------------------------------
# 5. ループでグラデーション
# ---------------------------------------------------------------------------
for i in range(5):
    t = i / 4  # 0.0 → 1.0
    bpy.ops.mesh.primitive_cube_add(size=0.6, location=(i * 1.0, -2.5, 0.3))
    cube = bpy.context.active_object
    cube.name = f"S03_Grad_{i}"
    color = (t, 0.3, 1.0 - t)  # 青 → 赤
    cube.data.materials.append(make_material(f"S03_Grad_{i}", color))

# ヒント: 入力名が分からないときは、ノードの入力を全部表示してみる
print("Principled BSDF の入力一覧:")
print("  " + ", ".join(inp.name for inp in bsdf.inputs))
