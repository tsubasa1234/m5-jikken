#include <Arduino.h>
#include <M5Unified.h>

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);

  M5.Display.setRotation(1);   // 横向き
  M5.Display.setTextSize(2);
  M5.Display.println("Hello World");
}

void loop() {
  M5.update();
}