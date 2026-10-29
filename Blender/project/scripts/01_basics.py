"""01: 基本 ― Blender の中身を Python から覗いてみる

【実行方法】
    このファイルを VSCode で開いた状態で Ctrl+Shift+B
    → print() の結果が VSCode のターミナルに表示される

【このサンプルで分かること】
    - bpy (Blender Python API) の 3 つの入口
        bpy.data    : .blend ファイルに保存されている全データ (オブジェクト、メッシュ、マテリアル…)
        bpy.context : 「今」の状態 (アクティブなシーン、選択中のオブジェクト…)
        bpy.ops     : メニューやボタンと同じ「操作」 (オブジェクト追加、削除…)
    - オブジェクトの名前・種類・位置の読み方

このスクリプトは何も変更しない (読むだけ) ので、何回実行しても安全。
"""

import bpy  # Blender の機能はすべてこのモジュールから使う

# ---------------------------------------------------------------------------
# 1. Blender 自体の情報
# ---------------------------------------------------------------------------
print("Blender バージョン:", bpy.app.version_string)
print("開いているファイル:", bpy.data.filepath or "(未保存)")

# ---------------------------------------------------------------------------
# 2. bpy.context : 今のシーン
# ---------------------------------------------------------------------------
scene = bpy.context.scene
print()
print("シーン名      :", scene.name)
print("フレーム範囲  :", scene.frame_start, "〜", scene.frame_end)
print("現在のフレーム:", scene.frame_current)

# ---------------------------------------------------------------------------
# 3. bpy.data : シーンにあるオブジェクトを一覧表示
# ---------------------------------------------------------------------------
print()
print(f"オブジェクト数: {len(bpy.data.objects)}")
for obj in bpy.data.objects:
    # obj.type は "MESH" / "CAMERA" / "LIGHT" / "EMPTY" などの文字列
    # obj.location は Vector 型。x, y, z で個別に取り出せる
    loc = obj.location
    print(f"  {obj.name:<20} 種類={obj.type:<8} 位置=({loc.x:.2f}, {loc.y:.2f}, {loc.z:.2f})")

# ---------------------------------------------------------------------------
# 4. 名前でオブジェクトを取り出す
#    bpy.data.objects["名前"] だと存在しないとき KeyError になるので、
#    .get("名前") を使って None チェックするのが安全
# ---------------------------------------------------------------------------
print()
cube = bpy.data.objects.get("Cube")
if cube is None:
    print('"Cube" という名前のオブジェクトはありません')
else:
    print('"Cube" の寸法   :', tuple(round(v, 3) for v in cube.dimensions))
    print('"Cube" の頂点数 :', len(cube.data.vertices))  # obj.data がメッシュ本体

# ---------------------------------------------------------------------------
# 5. 選択中のオブジェクト
#    Blender の画面でオブジェクトをクリックしてから実行すると結果が変わる
# ---------------------------------------------------------------------------
print()
selected = [o.name for o in bpy.context.view_layer.objects if o.select_get()]
print("選択中:", selected or "(なし)")
active = bpy.context.view_layer.objects.active
print("アクティブ:", active.name if active else "(なし)")

# ---------------------------------------------------------------------------
# ヒント: 使える属性を調べたいとき
#   dir(obj) で一覧が出る。Blender の画面でプロパティにマウスを乗せると
#   ツールチップに Python のパス (例: bpy.data.objects["Cube"].location) も出る
#   (表示されない場合: 編集 → プリファレンス → インターフェース → 「Python ツールチップ」を ON)
# ---------------------------------------------------------------------------
