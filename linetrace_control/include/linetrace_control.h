// linetrace_control.h
// ライントレース制御ロジック（Webots C / Arduino C++ 共通）
// センサ値を入れると左右モータ出力（-1.0〜1.0）を返す。
// センサ0番が左端、番号が増えるほど右側に並んでいる前提。

#ifndef LINETRACE_CONTROL_H
#define LINETRACE_CONTROL_H

#include <math.h>

#ifndef LT_NUM_SENSORS
#define LT_NUM_SENSORS 8   // e-puck で試すときは include 前に 3 を define
#endif

#define LT_LOST_THRESHOLD 0.3f  // センサ合計がこれ未満なら「ライン見失い」

typedef struct {
  float kp, kd;          // PDゲイン
  float base_speed;      // 直線での速度（0〜1）
  float slow_gain;       // ずれが大きいほど減速する割合（0〜1）
  float prev_error;
  float last_error;      // 最後にラインを見た位置（見失い時に使う）
  float sens_min[LT_NUM_SENSORS];
  float sens_max[LT_NUM_SENSORS];
} LtController;

static inline float lt_clamp(float v, float lo, float hi) {
  return v < lo ? lo : (v > hi ? hi : v);
}

static inline void lt_init(LtController* c, float kp, float kd,
                           float base_speed, float slow_gain) {
  c->kp = kp; c->kd = kd;
  c->base_speed = base_speed; c->slow_gain = slow_gain;
  c->prev_error = 0; c->last_error = 0;
  for (int i = 0; i < LT_NUM_SENSORS; i++) {
    c->sens_min[i] = 1e9f;
    c->sens_max[i] = -1e9f;
  }
}

// キャリブレーション：起動直後に車体を左右に振りながら何度も呼ぶ
static inline void lt_calibrate(LtController* c, const float raw[]) {
  for (int i = 0; i < LT_NUM_SENSORS; i++) {
    if (raw[i] < c->sens_min[i]) c->sens_min[i] = raw[i];
    if (raw[i] > c->sens_max[i]) c->sens_max[i] = raw[i];
  }
}

// ライン位置を -1.0（左端）〜 +1.0（右端）で返す。見失ったら found=0
// 黒で値が大きくなるセンサ前提。逆なら v = 1.0f - v にする。
static inline float lt_line_position(const LtController* c,
                                     const float raw[], int* found) {
  float sum = 0, wsum = 0;
  const float center = (LT_NUM_SENSORS - 1) / 2.0f;
  for (int i = 0; i < LT_NUM_SENSORS; i++) {
    float range = c->sens_max[i] - c->sens_min[i];
    float v = range > 0 ? (raw[i] - c->sens_min[i]) / range : 0;
    v = lt_clamp(v, 0, 1);
    sum += v;
    wsum += v * (i - center);
  }
  if (sum < LT_LOST_THRESHOLD) { *found = 0; return 0; }
  *found = 1;
  return (wsum / sum) / center;
}

// 制御周期ごとに呼ぶ。dt は秒。
static inline void lt_update(LtController* c, const float raw[], float dt,
                             float* left, float* right) {
  int found;
  float e = lt_line_position(c, raw, &found);

  if (found) {
    c->last_error = e;
  } else {
    // 見失ったら最後に見た側へ全力で曲がる
    e = (c->last_error >= 0) ? 1.0f : -1.0f;
  }

  float d = (dt > 0) ? (e - c->prev_error) / dt : 0;
  c->prev_error = e;

  float u = c->kp * e + c->kd * d;

  // カーブ（ずれ大）では減速、直線では base_speed
  float speed = c->base_speed * (1.0f - c->slow_gain * fabsf(e));

  *left  = lt_clamp(speed + u, -1, 1);
  *right = lt_clamp(speed - u, -1, 1);
}

#endif // LINETRACE_CONTROL_H
