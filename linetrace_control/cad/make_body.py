# FreeCAD マクロ: ライントレースカーのボディ（Chassis）とボール（Skid）を作る
# 使い方: FreeCAD でマクロ実行 → 続けて replace_skid_with_screws.py を実行すると

# 座標系: +X が前、Y が左右、Z=0 が床
#   前方(+X) … ラインセンサ取付
#   X=0      … 左右モータ（N20 + φ32 ホイール想定 → 車軸 Z=16）
#   X=-34    … ボール（Skid、φ8 → 中心 Z=4、上端がベース板下面 Z=8）
import FreeCAD as App
import Part

# ---- パラメータ（mm） ----
# ベース板（replace_skid_with_screws と同じ値にしておくこと）
PLATE_X0 = -45.0      # 後端
PLATE_X1 = 75.0       # 前端
PLATE_W = 76.0        # 幅（ホイールは板の外側に出る）
PLATE_Z0 = 8.0        # 下面
PLATE_T = 2.5         # 厚み（上面は 10.5）
CORNER_R = 6.0        # 角の丸め

# モータ（N20 ギアモータ想定: 断面 12 x 10、ホイール φ32）
WHEEL_D = 32.0
MOTOR_W = 12.0        # X方向
MOTOR_H = 10.0        # Z方向
MOTOR_Y_IN = 4.0      # 中央側の端（左右モータの隙間の半分）
MOTOR_Y_OUT = 30.0    # 外側の端（ギアボックス端）
CRADLE_WALL = 2.5     # 受け台の壁厚
TIE_W = 3.0           # 結束バンド穴の幅
TIE_L = 5.0

# ボール（Skid）
SKID_X = -34.0
SKID_D = 8.0
OLD_HOLE_R = 2.2      # ボール軸が通る穴の半径
SKID_SHAFT_R = 2.0

# ネジ穴共通
M3_D = 3.2            # 3Dプリントで M3 を通すなら 3.2〜3.4

# M5Stack 取付穴（実機で要実測）
M5_CX = 38.0
M5_PITCH_X = 44.0
M5_PITCH_Y = 44.0

# ラインセンサ取付穴（前端付近、板の下にセンサ基板を付ける）
SENSOR_X = 68.0
SENSOR_PITCH_Y = 40.0

# 配線穴（センサ → 上面）
WIRE_X = 60.0
WIRE_W = 6.0
WIRE_L = 16.0

AXLE_Z = WHEEL_D / 2   # 車軸の高さ（床からホイール半径）


def rounded_plate():
    """角を丸めた長方形の板"""
    L = PLATE_X1 - PLATE_X0
    box = Part.makeBox(L, PLATE_W, PLATE_T, App.Vector(PLATE_X0, -PLATE_W / 2, PLATE_Z0))
    vertical = [e for e in box.Edges
                if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
    return box.makeFillet(CORNER_R, vertical)


def through_hole(x, y, d):
    return Part.makeCylinder(d / 2, PLATE_T + 4, App.Vector(x, y, PLATE_Z0 - 2))


def through_slot(x, y, lx, ly):
    return Part.makeBox(lx, ly, PLATE_T + 4,
                        App.Vector(x - lx / 2, y - ly / 2, PLATE_Z0 - 2))


def motor_cradle(side):
    """モータを下半分だけ抱える受け台（side = +1 左 / -1 右）"""
    top = PLATE_Z0 + PLATE_T
    y0 = min(side * MOTOR_Y_IN, side * MOTOR_Y_OUT)
    ly = MOTOR_Y_OUT - MOTOR_Y_IN
    bw = MOTOR_W + 2 * CRADLE_WALL
    bh = AXLE_Z - top              # 受け台の高さ = 車軸まで
    block = Part.makeBox(bw, ly, bh, App.Vector(-bw / 2, y0, top))
    pocket = Part.makeBox(MOTOR_W, ly + 2, MOTOR_H,
                          App.Vector(-MOTOR_W / 2, y0 - 1, AXLE_Z - MOTOR_H / 2))
    return block.cut(pocket)


doc = App.newDocument("LineTraceCar")

# 1) ベース板 + モータ受け台
shape = rounded_plate()
for side in (+1, -1):
    shape = shape.fuse(motor_cradle(side))

# 2) 穴あけ
holes = []
#   ボール軸の穴
holes.append(Part.makeCylinder(OLD_HOLE_R, PLATE_T + 4, App.Vector(SKID_X, 0, PLATE_Z0 - 2)))
#   M5Stack
for sx in (-1, 1):
    for sy in (-1, 1):
        holes.append(through_hole(M5_CX + sx * M5_PITCH_X / 2, sy * M5_PITCH_Y / 2, M3_D))
#   ラインセンサ
for sy in (-1, 1):
    holes.append(through_hole(SENSOR_X, sy * SENSOR_PITCH_Y / 2, M3_D))
#   センサ配線
holes.append(through_slot(WIRE_X, 0, WIRE_W, WIRE_L))
#   モータ固定用の結束バンド穴（受け台の前後）
y_mid = (MOTOR_Y_IN + MOTOR_Y_OUT) / 2
x_tie = MOTOR_W / 2 + CRADLE_WALL + TIE_W / 2 + 0.5
for side in (+1, -1):
    for sx in (-1, 1):
        holes.append(through_slot(sx * x_tie, side * y_mid, TIE_W, TIE_L))

for h in holes:
    shape = shape.cut(h)

chassis = doc.addObject("Part::Feature", "Chassis")
chassis.Shape = shape.removeSplitter()

# 3) ボール（Skid）: 球 + 板を貫く軸
ball = Part.makeSphere(SKID_D / 2, App.Vector(SKID_X, 0, SKID_D / 2))
shaft = Part.makeCylinder(SKID_SHAFT_R, PLATE_Z0 + PLATE_T + 2 - SKID_D / 2,
                          App.Vector(SKID_X, 0, SKID_D / 2))
skid = doc.addObject("Part::Feature", "Skid")
skid.Shape = ball.fuse(shaft).removeSplitter()

doc.recompute()
if App.GuiUp:
    import FreeCADGui as Gui
    Gui.ActiveDocument.ActiveView.viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
print("done: Chassis %.0f x %.0f mm, axle Z=%.1f" % (PLATE_X1 - PLATE_X0, PLATE_W, AXLE_Z))
