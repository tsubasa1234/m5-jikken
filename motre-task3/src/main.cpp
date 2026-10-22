#include <M5StickCPlus.h>
#include <Wire.h>

uint8_t ADDR = 0x60;  // 要確認（スキャン結果に合わせる）

void drv(uint8_t vset, uint8_t dir) {      // vset: 0x06〜0x3F, dir: 0〜3
  Wire.beginTransmission(ADDR);
  Wire.write(0x00);                        // CONTROLレジスタ
  Wire.write((vset << 2) | dir);
  Wire.endTransmission();
}

void setup() {
  M5.begin();
  Wire.begin(32, 33);                      // SDA, SCL（要確認）
  for (uint8_t a = 1; a < 127; a++) {      // I2Cスキャン
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) Serial.printf("found 0x%02X\n", a);
  }
}

void loop() {
  drv(0x20, 1); delay(2000);               // 正転
  drv(0x00, 3); delay(500);                // ブレーキ
  drv(0x20, 2); delay(2000);               // 逆転
  drv(0x00, 0); delay(1000);               // 空転
}