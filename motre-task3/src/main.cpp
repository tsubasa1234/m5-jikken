#include <M5StickCPlus.h>
#include <Wire.h>

const uint8_t ADDR_LEFT  = 0x63;  // 左タイヤのモータ
const uint8_t ADDR_RIGHT = 0x65;  // 右タイヤのモータ
const uint8_t SPEED_LEFT  = 0x30;  // vset: 0x06〜0x3F。左が弱いので右より高め
const uint8_t SPEED_RIGHT = 0x10;

uint8_t drv(uint8_t addr, uint8_t vset, uint8_t dir) {
  Wire.beginTransmission(addr);
  Wire.write(0x00);
  Wire.write((vset << 2) | dir);
  return Wire.endTransmission();  // 0:成功 2:アドレスNACK 3:データNACK 4/5:その他・タイムアウト
}

void show(const char* state, uint8_t eL, uint8_t eR) {
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.setTextSize(3);
  M5.Lcd.println(state);
  M5.Lcd.setTextSize(2);
  M5.Lcd.printf("L(0x%02X) err=%d\n", ADDR_LEFT, eL);
  M5.Lcd.printf("R(0x%02X) err=%d\n", ADDR_RIGHT, eR);
}

// dirLeft/dirRight: 0:空転 1:正転 2:逆転 3:ブレーキ。止める側は vset=0 でブレーキ
void step(const char* label, uint8_t dirLeft, uint8_t dirRight, uint32_t ms) {
  uint8_t eL = drv(ADDR_LEFT, dirLeft == 3 ? 0 : SPEED_LEFT, dirLeft);
  if (dirRight == 1 || dirRight == 2) dirRight ^= 3;   // 右モータは配線が逆向きなので正転/逆転を入れ替える
  uint8_t eR = drv(ADDR_RIGHT, dirRight == 3 ? 0 : SPEED_RIGHT, dirRight);
  show(label, eL, eR);
  delay(ms);
}

void setup() {
  M5.begin();
  M5.Lcd.setRotation(3);
  Wire.begin(0, 26);

  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextSize(2);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.println("I2C scan:");
  int n = 0;
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) {
      M5.Lcd.printf("0x%02X ", a);
      Serial.printf("found 0x%02X\n", a);
      n++;
    }
  }
  if (n == 0) M5.Lcd.println("none");
  delay(3000);                             // スキャン結果を読む時間

  show("STOP", drv(ADDR_LEFT, 0, 0), drv(ADDR_RIGHT, 0, 0));
}

void loop() {
  M5.update();
  if (M5.BtnA.wasPressed()) {
    step("FWD",   1, 1, 1000);               // 前進
    step("STOP",  3, 3, 1000);               // 停止
    step("RIGHT", 3, 1, 500);               // 右回転（右タイヤだけ正転）
    step("LEFT",  1, 3, 500);               // 左回転（左タイヤだけ正転）
    step("BACK",  2, 2, 1000);               // 後退
    step("LEFT",  1, 3, 500);               // 左回転（左タイヤだけ正転）
    step("FWD",   1, 1, 1000);               // 前進
    step("STOP",  3, 3, 0);                  // 停止
  }
  delay(10);
}
