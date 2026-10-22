// 応用電子工学実験 第2回: 規定課題② 1モータの回転速度・回転方向制御
// M5ボタン (BtnA) を押すと課題②を1回実行する。
// Arduino-ESP32 core 2.x の API (ledcSetup / ledcAttachPin / ledcWrite(ch, duty)) を使用。
#include <Arduino.h>
#include <M5StickCPlus.h>

// ---- 設定 ----
const int PIN_A = 26;          // 前回転側
const int PIN_B = 0;           // 後回転側 (Groveが無いのでG0)
const uint8_t CH_A = 0;
const uint8_t CH_B = 1;
const uint32_t PWM_FREQ = 1000;    // 1kHz。20kHzより低速で回りやすい
const uint8_t  PWM_BITS = 8;       // duty 0..255
const int HIGH_SPEED    = 255;
// 上側MOSFETがソースフォロワになるため、モータには最大でも1V程度しかかからない。
// そのため反転は duty 最大 (255) で回す。
const int REV_SPEED     = 255;
const int REV_LOW_SPEED = 180;     // 低速後回転。低すぎると回らないので 180 程度
const uint32_t DEAD_TIME_MS = 5;   // 方向切り替え時に A/B を両方OFFにしておく時間

// ---- 表示 (M5StickC Plus: 横向き 240x135) ----
void showTitle(const char* title) {
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextDatum(MC_DATUM);
  M5.Lcd.setTextSize(2);
  M5.Lcd.setTextColor(CYAN, BLACK);
  M5.Lcd.drawString(title, M5.Lcd.width() / 2, 11);
}

void showState(const char* state) {
  int cy = M5.Lcd.height() / 2 - 3;
  M5.Lcd.fillRect(0, cy - 13, M5.Lcd.width(), 26, BLACK);
  M5.Lcd.setTextDatum(MC_DATUM);
  M5.Lcd.setTextSize(3);
  M5.Lcd.setTextColor(WHITE, BLACK);
  M5.Lcd.drawString(state, M5.Lcd.width() / 2, cy);
}

void showDuty(int duty) {          // -255..255 (負は後進。バーを赤で表示)
  const int NUM_W = 48;
  int y = M5.Lcd.height() - 22;
  int barW = M5.Lcd.width() - NUM_W - 8;
  int w = abs(duty) * barW / 255;
  M5.Lcd.fillRect(4 + w, y, barW - w, 18, DARKGREY);
  M5.Lcd.fillRect(4, y, w, 18, duty < 0 ? RED : GREEN);

  char buf[8];
  snprintf(buf, sizeof(buf), "%4d", duty);
  M5.Lcd.setTextDatum(MR_DATUM);
  M5.Lcd.setTextSize(2);
  M5.Lcd.setTextColor(YELLOW, BLACK);
  M5.Lcd.drawString(buf, M5.Lcd.width() - 2, y + 9);
}

// ---- モータ駆動 ----
// A と B が同時にONになると電池が短絡するので、方向を切り替えるときは
// 一度両方0にしてデッドタイムを置いてから新しい方向の出力を出す。
int lastDir = 0;                   // 1:前進, -1:後進, 0:停止

void drive(int speed) {            // -255..255 (正:前進, 負:後進)
  speed = constrain(speed, -255, 255);
  int dir = (speed > 0) - (speed < 0);
  if (dir != lastDir) {
    ledcWrite(CH_A, 0);
    ledcWrite(CH_B, 0);
    delay(DEAD_TIME_MS);
    lastDir = dir;
  }
  if (speed > 0)      { ledcWrite(CH_B, 0);      ledcWrite(CH_A, speed); }
  else if (speed < 0) { ledcWrite(CH_A, 0);      ledcWrite(CH_B, -speed); }
  else                { ledcWrite(CH_A, 0);      ledcWrite(CH_B, 0); }
  showDuty(speed);
}

// ---- 規定課題② ----
// 表示 → モータ出力 → ms だけ待つ。待っている間に上のボタン (BtnB) が押されたら
// すぐに停止して false を返す。
bool step(const char* label, int speed, uint32_t ms) {
  showState(label);
  drive(speed);
  uint32_t start = millis();
  while (millis() - start < ms) {
    M5.update();
    if (M5.BtnB.wasPressed()) {
      drive(0);
      return false;
    }
    delay(10);
  }
  return true;
}

// 停止 → 前回転 → 停止 → 後回転 → 低速後回転 → 停止 を1周期とし、loop() から繰り返し呼ぶ
// 途中で BtnB が押されたら false を返す
bool task2() {
  return step("FWD HI", HIGH_SPEED,     1000)   // 前回転 1秒
      && step("STOP",   0,              3000)   // 停止 3秒
      && step("REV HI", -REV_SPEED,     1000)   // 後回転 1秒
      && step("REV LO", -REV_LOW_SPEED, 1000)   // 低速後回転 1秒
      && step("STOP",   0,              1000);  // 停止 1秒
}

void setup() {
  // 起動直後にMOSFETが勝手にONにならないよう、最初にLOWに固定する
  pinMode(PIN_A, OUTPUT);
  digitalWrite(PIN_A, LOW);
  pinMode(PIN_B, OUTPUT);
  digitalWrite(PIN_B, LOW);

  M5.begin();
  M5.Lcd.setRotation(3);   // 横向き
  ledcSetup(CH_A, PWM_FREQ, PWM_BITS);
  ledcSetup(CH_B, PWM_FREQ, PWM_BITS);
  ledcAttachPin(PIN_A, CH_A);
  ledcAttachPin(PIN_B, CH_B);
  drive(0);
  showTitle("TASK 2");
  showState("PRESS M5");
}

bool running = false;

void loop() {
  // 正面の M5 ボタン (BtnA) を押すと、以降は課題②を無限に繰り返す
  // 上のボタン (BtnB) を押すと停止して、BtnA 待ちに戻る
  if (!running) {
    M5.update();
    if (M5.BtnA.wasPressed()) {
      showState("START");
      delay(2000);   // ボタンから手を離す猶予
      running = true;
    }
    delay(10);
    return;
  }
  if (!task2()) {
    running = false;
    showState("PRESS M5");
  }
}
