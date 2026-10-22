#include <FakeM5.h>

void setup() {
  M5.begin();
  M5.Lcd.setTextSize(2);
  M5.Lcd.println("Hello M5");
}

void loop() {
  M5.update();
}
