#pragma once
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>

#ifndef BLACK
#define BLACK  ILI9341_BLACK
#define WHITE  ILI9341_WHITE
#define RED    ILI9341_RED
#define GREEN  ILI9341_GREEN
#define BLUE   ILI9341_BLUE
#define YELLOW ILI9341_YELLOW
#endif

// M5Stack/M5StickC のコードでよく使う TFT_ 系の色名
#ifndef TFT_BLACK
#define TFT_BLACK  ILI9341_BLACK
#define TFT_WHITE  ILI9341_WHITE
#define TFT_RED    ILI9341_RED
#define TFT_GREEN  ILI9341_GREEN
#define TFT_BLUE   ILI9341_BLUE
#define TFT_YELLOW ILI9341_YELLOW
#endif

class FakeLcd : public Adafruit_ILI9341 {
public:
  FakeLcd() : Adafruit_ILI9341(14, 27, 33) {}  // CS, DC, RST（M5Stackと同じピン）
  void clear(uint16_t c = BLACK) { fillScreen(c); setCursor(0, 0); }
};

class FakeButton {
  uint8_t pin;
  bool last = HIGH, pressed = false, released = false;
public:
  FakeButton(uint8_t p) : pin(p) {}
  void begin() { pinMode(pin, INPUT_PULLUP); }
  void read() {
    bool s = digitalRead(pin);
    pressed  = (last == HIGH && s == LOW);   // 押した瞬間
    released = (last == LOW  && s == HIGH);  // 離した瞬間
    last = s;
  }
  bool wasPressed()  { return pressed; }
  bool wasReleased() { return released; }
  bool isPressed()   { return digitalRead(pin) == LOW; }
  bool isReleased()  { return digitalRead(pin) == HIGH; }
};

struct FakeM5 {
  FakeLcd Lcd;
  FakeButton BtnA{26}, BtnB{25}, BtnC{4};
  void begin() {
    Serial.begin(115200);
    Lcd.begin(); Lcd.setRotation(1); Lcd.fillScreen(BLACK);
    BtnA.begin(); BtnB.begin(); BtnC.begin();
  }
  void update() { BtnA.read(); BtnB.read(); BtnC.read(); delay(10); }
};

static FakeM5 M5;