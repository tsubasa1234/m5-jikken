import bpy

# 消したいオブジェクトを名前で取る（無ければ None）
obj = bpy.data.objects.get("Cube")

if obj is not None:
    mesh = obj.data if obj.type == "MESH" else None  # 先にメッシュデータを控えておく（オブジェクトを消すと obj は使えなくなる）
    bpy.data.objects.remove(obj, do_unlink=True)

    # メッシュデータも消したいとき（どのオブジェクトからも使われなくなった後）
    if mesh is not None and mesh.users == 0:
        bpy.data.meshes.remove(mesh)
else:
    print("Cube が見つかりません")

# ops で選択中を全部消す
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
