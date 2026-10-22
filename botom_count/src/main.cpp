#include <FakeM5.h>

int count = 0;

void show(const char* label,uint16_t bg,uint16_t fg){
  M5.Lcd.fillScreen(bg);
  M5.Lcd.setTextColor(fg);
  M5.Lcd.setTextSize(3);
  M5.Lcd.setCursor(10, 100);
  M5.Lcd.printf("%s: %d",label, count);
}

void setup() {
  M5.begin();
  show("Count",BLACK,WHITE);
}

void loop() {
  M5.update();
  if(M5.BtnA.wasReleased()){
    count++;
    show("Count Up",RED,YELLOW);
  }
  if (M5.BtnB.wasReleased()){
    count = 0;
    show("Count Reset",BLACK,WHITE);
  }
  if (M5.BtnC.wasReleased()){
    if(count > 0) count--;
    show("Count Down",GREEN,BLACK);
  }
}
