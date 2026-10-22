// ライントレース制御の Wokwi テスト
//   ポテンショメータ5個 = ラインセンサ（S0 左端 〜 S4 右端、回すほど「黒」）
//   青LED2個 = 左右モータ（明るさ = 出力）
//   A: キャリブレーション開始/終了（その間に全ポテを端から端まで回す）
//   B: 走行開始/停止

#define LT_NUM_SENSORS 5
#include <FakeM5.h>
#include "linetrace_control.h"

const int SENSOR_PINS[LT_NUM_SENSORS] = {32, 33, 34, 35, 36};  // 36 = VP
const int MOTOR_L_PIN = 16;
const int MOTOR_R_PIN = 4;

const float KP = 0.8f;
const float KD = 0.05f;
const float BASE_SPEED = 0.6f;
const float SLOW_GAIN = 0.5f;

enum Mode { IDLE, CALIB, RUN };
Mode mode = IDLE;

LtController ctl;
float raw[LT_NUM_SENSORS];
float outL = 0, outR = 0;
unsigned long lastMicros = 0;
unsigned long lastDraw = 0;

void readSensors() {
  for (int i = 0; i < LT_NUM_SENSORS; i++) raw[i] = analogRead(SENSOR_PINS[i]);
}

// -1〜1 の出力を LED の明るさに（後退は消灯で表現）
void driveMotors(float l, float r) {
  analogWrite(MOTOR_L_PIN, (int)(lt_clamp(l, 0, 1) * 255));
  analogWrite(MOTOR_R_PIN, (int)(lt_clamp(r, 0, 1) * 255));
}

void drawScreen() {
  const char* names[] = {"IDLE  ", "CALIB ", "RUN   "};
  M5.Lcd.setTextSize(2);
  M5.Lcd.setTextColor(WHITE, BLACK);
  M5.Lcd.setCursor(10, 10);
  M5.Lcd.printf("Mode: %s", names[mode]);

  // センサ値を正規化してバー表示
  for (int i = 0; i < LT_NUM_SENSORS; i++) {
    float range = ctl.sens_max[i] - ctl.sens_min[i];
    float v = range > 0 ? lt_clamp((raw[i] - ctl.sens_min[i]) / range, 0, 1) : 0;
    int x = 20 + i * 58, h = (int)(v * 100);
    M5.Lcd.fillRect(x, 50, 40, 100 - h, BLACK);
    M5.Lcd.fillRect(x, 50 + 100 - h, 40, h, YELLOW);
    M5.Lcd.drawRect(x, 50, 40, 100, WHITE);
  }

  int found;
  float pos = lt_line_position(&ctl, raw, &found);
  M5.Lcd.setCursor(10, 165);
  if (found) M5.Lcd.printf("Pos: %+5.2f     ", pos);
  else       M5.Lcd.printf("Pos: LOST       ");
  M5.Lcd.setCursor(10, 195);
  M5.Lcd.printf("L:%+5.2f R:%+5.2f", outL, outR);
}

void setup() {
  M5.begin();
  pinMode(MOTOR_L_PIN, OUTPUT);  // BtnC(4) の INPUT_PULLUP を上書き
  pinMode(MOTOR_R_PIN, OUTPUT);
  driveMotors(0, 0);
  lt_init(&ctl, KP, KD, BASE_SPEED, SLOW_GAIN);
  Serial.println("A: calib, B: start/stop");
}

void loop() {
  M5.update();
  readSensors();

  if (M5.BtnA.wasPressed()) {
    if (mode == CALIB) {
      mode = IDLE;
    } else {
      lt_init(&ctl, KP, KD, BASE_SPEED, SLOW_GAIN);
      mode = CALIB;
    }
  }
  if (M5.BtnB.wasPressed()) {
    if (mode == RUN) {
      mode = IDLE;
    } else {
      ctl.prev_error = 0;
      lastMicros = micros();
      mode = RUN;
    }
  }

  if (mode == CALIB) {
    lt_calibrate(&ctl, raw);
  } else if (mode == RUN) {
    unsigned long now = micros();
    float dt = (now - lastMicros) / 1e6f;
    lastMicros = now;
    lt_update(&ctl, raw, dt, &outL, &outR);
  }
  if (mode != RUN) outL = outR = 0;
  driveMotors(outL, outR);

  if (millis() - lastDraw > 100) {
    lastDraw = millis();
    drawScreen();
    Serial.printf("%d %d %d %d %d  L=%+.2f R=%+.2f\n",
                  (int)raw[0], (int)raw[1], (int)raw[2], (int)raw[3], (int)raw[4],
                  outL, outR);
  }
}
