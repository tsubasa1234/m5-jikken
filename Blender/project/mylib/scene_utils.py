"""サンプルスクリプトで共通して使う便利関数

scripts/ 内のファイルから
    from mylib.scene_utils import reset_collection
のように import して使う。
(send_to_blender.py がプロジェクトルートを sys.path に追加するので import できる)

このファイルを編集して保存し、もう一度 Ctrl+Shift+B を押すと
Blender を再起動しなくても変更が反映される。
"""

import bpy


def reset_collection(name):
    """name という名前のコレクションを空の状態で用意して返す。

    サンプルは何度でも実行し直せるように、毎回このコレクションの中身を
    全部消してから作り直す。ほかのコレクションのオブジェクトには触らない。
    """
    collection = bpy.data.collections.get(name)
    if collection is None:
        # 新しいコレクションを作り、シーンのルートにぶら下げる
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    else:
        # 中のオブジェクトを削除 (do_unlink=True で全シーンから外して消す)
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    return collection


def new_object(name, mesh, collection, location=(0.0, 0.0, 0.0)):
    """メッシュデータからオブジェクトを作り、コレクションに入れて返す"""
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    collection.objects.link(obj)
    return obj


def make_material(name, color, metallic=0.0, roughness=0.5):
    """単色の Principled BSDF マテリアルを作って (既にあれば再利用して) 返す。

    color は (R, G, B) を 0.0〜1.0 で指定する。
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)  # RGBA
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*color, 1.0)  # ソリッド表示のときの色
    return mat
