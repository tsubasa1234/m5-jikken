#include<FakeM5.h>
#include"Ultrasonic.h"

Ultrasonic ultrasonic(16);

long RangeInCentimeters = 0;

void setup(){

  M5.begin();

}

void loop(){

  RangeInCentimeters = ultrasonic.MeasureInCentimeters();

  M5.Lcd.setCursor(10,70);
  M5.Lcd.setTextSize(3);
  M5.Lcd.printf("%3ld cm",RangeInCentimeters);

  delay(250);
}