#include <FakeM5.h>
#include "xbm_open.h"
#include "xbm_close.h"

void setup() {

  M5.begin();
  pinMode(36, INPUT_PULLUP);

  M5.Lcd.fillScreen(TFT_WHITE);
  M5.Lcd.drawXBitmap(M5.Lcd.width()/2 - logoWidth/2, 0, openlogo, logoWidth, logoHeight, TFT_GREEN);
  M5.Lcd.setRotation(1);

}

void loop() {
  if(digitalRead(36) == 1) {
    // 使用中
    M5.Lcd.fillScreen(TFT_WHITE);
    M5.Lcd.drawXBitmap(M5.Lcd.width()/2 - logoWidth/2, 0, closelogo, logoWidth, logoHeight, TFT_RED);
    delay(4000);
    M5.Lcd.fillScreen(TFT_WHITE);
  } else {
    // 空室
    M5.Lcd.drawXBitmap(M5.Lcd.width()/2 - logoWidth/2, 0, openlogo, logoWidth, logoHeight, TFT_GREEN);
  }
}
