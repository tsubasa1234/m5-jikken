# FreeCAD マクロ: ボール(Skid)を外して、その位置に M3 用のネジ穴を3つ開ける
# 使い方: FreeCAD でファイルを開き、マクロ実行（またはPythonコンソールに貼り付け）
import FreeCAD as App
import Part

# ---- パラメータ（mm） ----
CENTER_X = -34.0      # ボールがあった位置
CENTER_Y = 0.0
HOLE_D = 3.0          # ネジ穴の直径（3Dプリントなら 3.2〜3.4 も検討）
PITCH = 10.0          # 穴の中心間距離
N_HOLES = 3
PLATE_Z0 = 8.0        # ベース板の下面
PLATE_T = 2.5         # ベース板の厚み（上面は 10.5）
OLD_HOLE_R = 2.2      # ボール軸が通っていた古い穴の半径

doc = App.ActiveDocument
chassis = doc.getObject("Chassis")
shape = chassis.Shape

# 1) 古い穴を埋める（半径は少し大きめにして面の重なりを避ける）
fill = Part.makeCylinder(OLD_HOLE_R + 0.2, PLATE_T, App.Vector(CENTER_X, CENTER_Y, PLATE_Z0))
shape = shape.fuse(fill)

# 2) Y方向に等間隔で貫通穴を開ける
for i in range(N_HOLES):
    y = CENTER_Y + (i - (N_HOLES - 1) / 2) * PITCH
    hole = Part.makeCylinder(HOLE_D / 2, PLATE_T + 4, App.Vector(CENTER_X, y, PLATE_Z0 - 2))
    shape = shape.cut(hole)

# 3) 不要な分割面を整理して反映
chassis.Shape = shape.removeSplitter()

# 4) ボール(Skid)を削除
if doc.getObject("Skid"):
    doc.removeObject("Skid")

doc.recompute()
print("done: %d holes, D=%.1f, pitch=%.1f" % (N_HOLES, HOLE_D, PITCH))
