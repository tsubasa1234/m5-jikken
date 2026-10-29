"""06: 自作モジュールの使い方とエラーの見方

【実行方法】  Ctrl+Shift+B
【結果】      "Sample_06" コレクションに、mylib の関数で作った立方体が並ぶ

【このサンプルで分かること】
    - 自分で書いた関数を別ファイル (モジュール) に分けて import する方法
    - モジュールを編集したときの反映のされ方
    - エラーが起きたときに VSCode でどう表示されるか

-----------------------------------------------------------------------------
■ import の仕組み
    send_to_blender.py は実行のたびに、次のフォルダを Blender の sys.path に追加する。
        1. 実行したファイルのフォルダ   (例: project/scripts/)
        2. プロジェクトルート           (例: project/)       ← VSCode で開いたフォルダ
        3. プロジェクトルート/src       (あれば)
    なので、どのフォルダのスクリプトからでも
        from mylib.scene_utils import reset_collection
    のようにプロジェクトルートを基準に import できる。

    フォルダ構成の例:
        project/
        ├── mylib/              ← 自作モジュールの置き場所
        │   ├── __init__.py     ← 空でよい。「パッケージ」の印
        │   ├── scene_utils.py
        │   └── shapes.py
        ├── scripts/            ← Ctrl+Shift+B で実行するスクリプト
        └── tools/send_to_blender.py

■ モジュールを編集したら?
    project/ 以下のモジュールは実行のたびに読み込み直されるので、
    mylib/shapes.py を書き換えて保存 → このファイルに戻って Ctrl+Shift+B で反映される。
    (Blender の再起動は不要)
-----------------------------------------------------------------------------
"""

import bpy

from mylib import shapes  # モジュールごと import → shapes.add_cube() で呼ぶ
from mylib.scene_utils import make_material, reset_collection  # 関数だけ import

collection = reset_collection("Sample_06")
bpy.context.view_layer.active_layer_collection = (
    bpy.context.view_layer.layer_collection.children[collection.name])

green = make_material("S06_Green", (0.1, 0.7, 0.3))

for i in range(5):
    cube = shapes.add_cube(f"S06_Cube_{i}", location=(i * 1.5, 0.0, 0.5), size=0.8 + i * 0.1)
    cube.data.materials.append(green)

print("mylib.shapes の場所:", shapes.__file__)
print("このスクリプトの場所:", __file__)  # 送信元ファイルのパスが入っている


# ---------------------------------------------------------------------------
# ■ エラーの見方 (試してみよう)
#   下の行の先頭の # を消して Ctrl+Shift+B を押すと、わざとエラーが起きる。
#     - VSCode のターミナルにトラックバック (どこで何が起きたか) が表示される
#     - エラーの行に赤い波線が付き、「問題」パネル (⇧⌘M) にも一覧が出る
#   エラーが起きても Blender は落ちない。直して保存し、もう一度 Ctrl+Shift+B。
# ---------------------------------------------------------------------------
# bpy.data.objects["存在しない名前"]  # KeyError: 名前が見つからない


# ---------------------------------------------------------------------------
# ■ よくあるエラー
#   ModuleNotFoundError: No module named 'mylib'
#       → VSCode で project/ フォルダを開いているか確認 (プロジェクトルートが違うと見つからない)
#   AttributeError: 'NoneType' object has no attribute ...
#       → bpy.data.objects.get("名前") などが None を返している (名前の打ち間違い)
#   RuntimeError: Operator bpy.ops.xxx.poll() failed, context is incorrect
#       → その操作に必要な画面の状態 (context) が足りない。
#         with bpy.context.temp_override(...) で対象を指定するか、
#         bpy.ops を使わず bpy.data の API で書き直す
# ---------------------------------------------------------------------------
