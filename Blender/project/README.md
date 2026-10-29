# VSCode → Blender スクリプト実行環境

VSCode で書いた Python スクリプトを **Ctrl+Shift+B** で Blender に送り、すぐ実行するための環境です。

## 毎回の使い方

1. Blender を起動する（アドオン「VSCode Code Runner Server」が自動でサーバーを開始）
2. VSCode で **この `project/` フォルダ** を開く（「ファイル → フォルダーを開く」）
3. 実行したい `.py` ファイルを開いて **Ctrl+Shift+B**（または ⇧⌘B）
4. `print()` の結果やエラーは VSCode のターミナルに表示される

> 動かないときのチェック
> - Blender の 3D ビューで **N** キー → 「VSCode」タブが「待機中: 127.0.0.1:52525」になっているか
> - VSCode で開いているのが `Blender/` ではなく `Blender/project/` か

## フォルダ構成

```
project/
├── .vscode/tasks.json      Ctrl+Shift+B の設定
├── tools/send_to_blender.py  Blender へ送信するクライアント
├── mylib/                  自作モジュール (どのスクリプトからも import できる)
│   ├── scene_utils.py      reset_collection / make_material など
│   └── shapes.py
└── scripts/                サンプルスクリプト (番号順に読むのがおすすめ)
```

## サンプル一覧

| ファイル | 内容 |
|---|---|
| `scripts/01_basics.py` | bpy.data / bpy.context / bpy.ops の違い、オブジェクト一覧の表示（読むだけ） |
| `scripts/02_objects.py` | 追加・移動・回転・拡大・削除、頂点から自作メッシュ、ループで大量生成 |
| `scripts/03_materials.py` | マテリアルの作成と割り当て、金属・ガラス・発光、グラデーション |
| `scripts/04_modifiers.py` | サブディビジョン・ベベル・配列・ミラー・ソリッド化、重ねがけ |
| `scripts/05_animation.py` | キーフレーム、跳ねるボール、拡大縮小アニメーション |
| `scripts/06_modules_and_errors.py` | 自作モジュールの import の仕組み、エラーの見方とよくあるエラー |
| `scripts/hello_cube.py` | 動作確認用の最小サンプル |

各サンプルは `Sample_01` … のような専用コレクションの中だけを作り直すので、
何度実行しても増えず、ほかのオブジェクトも消えません。
（`05` だけはシーンのフレーム範囲と fps も変更します）

## 書き方の基本

```python
import bpy                                   # Blender の API

from mylib.scene_utils import reset_collection, make_material   # 自作モジュール

col = reset_collection("MyWork")             # 前回の結果を消して空のコレクションを用意
bpy.context.view_layer.active_layer_collection = (
    bpy.context.view_layer.layer_collection.children[col.name])  # 追加先をこのコレクションに

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.5))  # 追加
obj = bpy.context.active_object              # 追加したオブジェクトを受け取る
obj.name = "MyCube"
obj.rotation_euler.z = 0.785                 # 回転はラジアン (math.radians(45) と同じ)
obj.data.materials.append(make_material("MyRed", (0.8, 0.1, 0.1)))

print("できた:", obj.name)                   # VSCode のターミナルに出る
```

| やりたいこと | 書き方 |
|---|---|
| 名前でオブジェクトを取る | `bpy.data.objects.get("Cube")`（無ければ `None`） |
| 選択中のオブジェクト | `bpy.context.selected_objects` |
| 位置・回転・拡大 | `obj.location` / `obj.rotation_euler` / `obj.scale` |
| 削除 | `bpy.data.objects.remove(obj, do_unlink=True)` |
| モディファイア追加 | `obj.modifiers.new("名前", type="BEVEL")` |
| キーフレーム | `obj.keyframe_insert(data_path="location", frame=10)` |

### 調べ方のコツ

- Blender の「編集 → プリファレンス → インターフェース」で **Python ツールチップ** を ON にすると、
  ボタンやプロパティにマウスを乗せたときに Python での書き方が表示される
- 画面上で操作すると「情報」エディタに対応する `bpy.ops...` が記録されるので、コピーして使える
- `print(dir(obj))` で使える属性の一覧が見られる
- 公式リファレンス: https://docs.blender.org/api/current/

## 注意

- スクリプトは Blender のメインスレッドで動くため、重い処理の間は Blender の画面が止まる
- VSCode からの実行では画面の情報 (context) が限られるため、一部の `bpy.ops` は
  `with bpy.context.temp_override(object=obj): ...` で対象を指定する必要がある
- 未保存の変更は送られない（VSCode は通常タスク実行前に自動保存する）
