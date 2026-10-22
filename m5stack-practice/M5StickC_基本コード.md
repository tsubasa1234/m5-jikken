# M5StickC 基本コードの書き方まとめ

> 対象：M5StickC / M5StickC Plus / Plus2（Arduino IDE / PlatformIO）
> ライブラリは現行推奨の **M5Unified** を基本に、旧 `M5StickC.h` との違いも併記。

---

## 1. 開発環境の準備

### Arduino IDE
1. 環境設定 →「追加のボードマネージャのURL」に以下を追加
   `https://static-cdn.m5stack.com/resource/arduino/package_m5stack_index.json`
2. ボードマネージャで **M5Stack** をインストール
3. ライブラリマネージャで **M5Unified**（依存の M5GFX も）をインストール
4. ボード選択：`M5StickC` / `M5StickCPlus` / `M5StickCPlus2`

### PlatformIO（platformio.ini）
```ini
[env:m5stick-c]
platform = espressif32
board = m5stick-c
framework = arduino
monitor_speed = 115200
lib_deps = m5stack/M5Unified
```

---

## 2. 最小構成（テンプレート）

```cpp
#include <M5Unified.h>

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);            // 画面・ボタン・IMU・電源などを初期化

  M5.Display.setRotation(1);   // 0〜3（1 or 3 で横向き）
  M5.Display.setTextSize(2);
  M5.Display.println("Hello M5!");
}

void loop() {
  M5.update();              // ボタン状態の更新（loopの先頭で必ず呼ぶ）
  delay(10);
}
```

**ポイント**
- `M5.begin()` は `setup()` で1回
- `M5.update()` を呼ばないとボタン入力が取れない

---

## 3. 画面表示（Display）

画面サイズ：StickC = 80×160、Plus / Plus2 = 135×240

```cpp
M5.Display.fillScreen(BLACK);              // 画面クリア
M5.Display.setCursor(0, 0);                // カーソル位置
M5.Display.setTextColor(WHITE, BLACK);     // 文字色, 背景色
M5.Display.setTextSize(2);                 // 文字サイズ倍率
M5.Display.print("Temp: ");
M5.Display.printf("%.1f C\n", 25.3);       // printf も使える

// 図形
M5.Display.drawPixel(10, 10, RED);
M5.Display.drawLine(0, 0, 50, 50, GREEN);
M5.Display.drawRect(10, 10, 40, 20, BLUE);
M5.Display.fillRect(10, 40, 40, 20, YELLOW);
M5.Display.drawCircle(60, 60, 15, CYAN);
M5.Display.fillCircle(60, 60, 10, MAGENTA);

// 明るさ（0〜255）
M5.Display.setBrightness(128);

// 日本語フォント
M5.Display.setFont(&fonts::lgfxJapanGothic_16);
M5.Display.println("こんにちは");
```

> ちらつき対策には `M5Canvas`（スプライト）に描いてから `pushSprite()` する。

```cpp
M5Canvas canvas(&M5.Display);
canvas.createSprite(M5.Display.width(), M5.Display.height());
canvas.fillScreen(BLACK);
canvas.drawString("No flicker", 0, 0);
canvas.pushSprite(0, 0);
```

---

## 4. ボタン入力

| ボタン | 位置 | M5Unified |
|---|---|---|
| A | 正面の大きいボタン（M5ロゴ） | `M5.BtnA` |
| B | 右側面ボタン | `M5.BtnB` |
| 電源 | 左側面ボタン | `M5.BtnPWR`（Plus2等） |

```cpp
void loop() {
  M5.update();

  if (M5.BtnA.wasPressed())   M5.Display.println("A pressed");
  if (M5.BtnA.wasReleased())  M5.Display.println("A released");
  if (M5.BtnA.isPressed())    { /* 押している間ずっと */ }
  if (M5.BtnB.wasHold())      M5.Display.println("B hold"); // 長押し
  if (M5.BtnA.pressedFor(2000)) { /* 2秒以上押下 */ }
}
```

---

## 5. 内蔵LED

赤色LED：**G10**（LOWで点灯 / 負論理）※Plus2は **G19**（HIGHで点灯）

```cpp
const int LED_PIN = 10;

void setup() {
  M5.begin();
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_PIN, LOW);   // 点灯
  delay(500);
  digitalWrite(LED_PIN, HIGH);  // 消灯
  delay(500);
}
```

---

## 6. IMU（加速度・ジャイロ）

```cpp
float ax, ay, az, gx, gy, gz;

void loop() {
  M5.update();
  if (M5.Imu.update()) {
    M5.Imu.getAccel(&ax, &ay, &az);   // 単位: G
    M5.Imu.getGyro(&gx, &gy, &gz);    // 単位: deg/s

    M5.Display.setCursor(0, 0);
    M5.Display.printf("ax:%5.2f\nay:%5.2f\naz:%5.2f\n", ax, ay, az);
  }
  delay(50);
}
```

---

## 7. 電源・バッテリー

```cpp
int level   = M5.Power.getBatteryLevel();    // 残量 %
int voltage = M5.Power.getBatteryVoltage();  // mV
bool charging = M5.Power.isCharging();

M5.Power.powerOff();          // 電源OFF
M5.Power.deepSleep(10 * 1000000ULL); // 10秒ディープスリープ（μs）
```

---

## 8. ブザー（Plus / Plus2 のみ）

```cpp
M5.Speaker.tone(2000, 200);   // 2000Hz を 200ms
M5.Speaker.setVolume(128);    // 0〜255
```

---

## 9. シリアル通信（デバッグ）

```cpp
void setup() {
  M5.begin();
  Serial.begin(115200);
}

void loop() {
  Serial.printf("millis = %lu\n", millis());
  delay(1000);
}
```

---

## 10. GPIO・外部接続

| 端子 | 主なピン | 用途 |
|---|---|---|
| Grove（HY2.0） | G32（SDA）, G33（SCL） | I2C / 各種Unit |
| ヘッダ | G0, G26, G36 | デジタル/アナログ入出力 |
| 内部I2C | G21（SDA）, G22（SCL） | IMU・RTC・PMIC用（基本触らない） |

```cpp
// アナログ読み取り
int v = analogRead(36);

// 外部I2C（Grove）
#include <Wire.h>
Wire.begin(32, 33);
```

> G36 は入力専用。G0 は起動モードに関わるので注意。

---

## 11. Wi-Fi 接続

```cpp
#include <M5Unified.h>
#include <WiFi.h>

const char* SSID = "your-ssid";
const char* PASS = "your-password";

void setup() {
  M5.begin();
  WiFi.begin(SSID, PASS);
  M5.Display.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    M5.Display.print(".");
  }
  M5.Display.println("\nOK");
  M5.Display.println(WiFi.localIP());
}

void loop() {}
```

---

## 12. 非ブロッキングの書き方（delayを使わない）

```cpp
unsigned long prev = 0;
const unsigned long INTERVAL = 1000;

void loop() {
  M5.update();
  unsigned long now = millis();
  if (now - prev >= INTERVAL) {
    prev = now;
    // 1秒ごとの処理
  }
  // ボタン処理などはここで常に回る
}
```

---

## 13. 総合サンプル：ボタンでカウント＆傾き表示

```cpp
#include <M5Unified.h>

int count = 0;

void setup() {
  M5.begin();
  M5.Display.setRotation(1);
  M5.Display.setTextSize(2);
}

void loop() {
  M5.update();

  if (M5.BtnA.wasPressed()) count++;
  if (M5.BtnB.wasPressed()) count = 0;

  float ax, ay, az;
  M5.Imu.getAccel(&ax, &ay, &az);

  M5.Display.fillScreen(BLACK);
  M5.Display.setCursor(0, 0);
  M5.Display.printf("Count:%d\n", count);
  M5.Display.printf("X:%5.2f\nY:%5.2f\n", ax, ay);
  M5.Display.printf("Bat:%d%%\n", M5.Power.getBatteryLevel());

  delay(100);
}
```

---

## 付録：旧ライブラリ（M5StickC.h）との対応

| 機能 | 旧 `M5StickC.h` | 新 `M5Unified.h` |
|---|---|---|
| 初期化 | `M5.begin();` | `M5.begin(M5.config());` |
| 画面 | `M5.Lcd.xxx` | `M5.Display.xxx`（`M5.Lcd` も可） |
| IMU初期化 | `M5.IMU.Init();` | 不要（自動） |
| 加速度 | `M5.IMU.getAccelData(&x,&y,&z)` | `M5.Imu.getAccel(&x,&y,&z)` |
| バッテリー | `M5.Axp.GetBatVoltage()` | `M5.Power.getBatteryVoltage()` |
| 明るさ | `M5.Axp.ScreenBreath(n)` | `M5.Display.setBrightness(n)` |

> ネット上の古いサンプルは `M5StickC.h` が多い。機種間で同じコードを使い回せるので、新規なら M5Unified 推奨。

---

## よくあるハマりどころ

- **書き込めない** → USBケーブルがデータ通信対応か確認／ボーレートを下げる（115200など）
- **ボタンが反応しない** → `M5.update()` を呼び忘れ
- **画面が真っ暗** → 明るさ0、または電源ボタン長押し（6秒でOFF / 2秒でON）
- **文字が切れる** → `setRotation()` と画面サイズ（80×160 or 135×240）を確認
- **LEDが逆に光る** → StickC/Plus は負論理（LOWで点灯）
