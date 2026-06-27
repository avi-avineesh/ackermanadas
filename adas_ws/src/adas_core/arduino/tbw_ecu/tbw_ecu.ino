/*
 * tbw_ecu.ino — Throttle-By-Wire ECU Firmware
 * Target  : Arduino Uno
 * Crystal : 8 MHz
 * CAN     : MCP2515 via MCP_CAN (Cory J. Fowler), 500 kbps
 *
 * CAN RX  0x120 : speed_mms int16 BE (bytes 0-1)
 *                 brake_pct  uint8   (byte  2)
 *                 mode       uint8   (byte  3)  0=idle, 1=rc, 2=estop
 * CAN TX  0x220 : encL int32 BE (bytes 0-3), encR int32 BE (bytes 4-7)   @ 20 Hz
 * CAN TX  0x320 : rpmL int16 BE (bytes 0-1), rpmR int16 BE (bytes 2-3),
 *                 status uint8 (byte 4)                                    @ 10 Hz
 *
 * Pins
 *   MOT_L_PWM = 5  (D5,  PWM)
 *   MOT_L_DIR = 4  (D4)
 *   MOT_R_PWM = 6  (D6,  PWM)
 *   MOT_R_DIR = 7  (D7)
 *   CAN_CS    = 10 (D10, SPI)
 *   CAN_INT   = 2  (D2,  INT0)
 *   ENC_L_A   = A0 (PCINT8)
 *   ENC_L_B   = A1 (direction)
 *   ENC_R_A   = A2 (PCINT10)
 *   ENC_R_B   = A3 (direction)
 */

#include <SPI.h>
#include <mcp_can.h>

// ---------------------------------------------------------------------------
// Pin definitions
// ---------------------------------------------------------------------------
#define MOT_L_PWM  5
#define MOT_L_DIR  4
#define MOT_R_PWM  6
#define MOT_R_DIR  7
#define CAN_CS     10
#define CAN_INT    2
#define ENC_L_A    A0
#define ENC_L_B    A1
#define ENC_R_A    A2
#define ENC_R_B    A3

// ---------------------------------------------------------------------------
// CAN IDs
// ---------------------------------------------------------------------------
#define CAN_ID_RX_TBW   0x120
#define CAN_ID_TX_ENC   0x220
#define CAN_ID_TX_RPM   0x320

// ---------------------------------------------------------------------------
// Motor / PID constants
// ---------------------------------------------------------------------------
#define TICKS_PER_REV   148      // encoder ticks per wheel revolution
#define PID_RATE_MS     20      // PID runs every 20 ms → 50 Hz
#define ENC_TX_MS       50      // encoder TX every 50 ms  → 20 Hz
#define RPM_TX_MS       100     // RPM TX every 100 ms     → 10 Hz
#define WATCHDOG_MS     500     // no CAN → idle after 500 ms

static const float Kp = 0.15f;
static const float Ki = 0.02f;
static const float Kd = 0.01f;

// TBW mode bytes
#define MODE_IDLE   0
#define MODE_RC     1
#define MODE_ESTOP  2

// ---------------------------------------------------------------------------
// Global CAN object
// ---------------------------------------------------------------------------
MCP_CAN CAN(CAN_CS);

// ---------------------------------------------------------------------------
// Command state (set from CAN RX ISR / loop)
// ---------------------------------------------------------------------------
volatile int16_t  g_speed_mms   = 0;
volatile uint8_t  g_brake_pct   = 0;
volatile uint8_t  g_tbw_mode    = MODE_IDLE;
volatile uint32_t g_last_rx_ms  = 0;   // millis() of last 0x120 frame

// ---------------------------------------------------------------------------
// Encoder state (set from PCINT ISR)
// ---------------------------------------------------------------------------
volatile long g_enc_l_count = 0;
volatile long g_enc_r_count = 0;

// Snapshots for speed / RPM calculation
long     g_enc_l_prev_pid = 0;
long     g_enc_r_prev_pid = 0;
long     g_enc_l_prev_rpm = 0;
long     g_enc_r_prev_rpm = 0;

// ---------------------------------------------------------------------------
// PID state (per motor)
// ---------------------------------------------------------------------------
struct PidState {
    float integral   = 0.0f;
    float prev_error = 0.0f;
};

PidState g_pid_l;
PidState g_pid_r;

// ---------------------------------------------------------------------------
// Timing
// ---------------------------------------------------------------------------
uint32_t g_last_pid_ms  = 0;
uint32_t g_last_enc_ms  = 0;
uint32_t g_last_rpm_ms  = 0;

// ---------------------------------------------------------------------------
// CAN RX flag (set by INT0 ISR, cleared in loop)
// ---------------------------------------------------------------------------
volatile bool g_can_rx_flag = false;

// ===========================================================================
// ISRs
// ===========================================================================

// INT0 — MCP2515 interrupt (active-low)
void canRxISR() {
    g_can_rx_flag = true;
}

// PCINT1 — handles PCINT8..PCINT14 (Analog pins A0-A5)
ISR(PCINT1_vect) {
    // Left encoder (A0 = PCINT8)
    if (PINC & _BV(PC0)) {                  // rising edge on ENC_L_A
        if (PINC & _BV(PC1)) {              // ENC_L_B high → forward
            g_enc_l_count++;
        } else {
            g_enc_l_count--;
        }
    }

    // Right encoder (A2 = PCINT10)
    if (PINC & _BV(PC2)) {                  // rising edge on ENC_R_A
        if (PINC & _BV(PC3)) {              // ENC_R_B high → forward
            g_enc_r_count++;
        } else {
            g_enc_r_count--;
        }
    }
}

// ===========================================================================
// Motor helpers
// ===========================================================================

/**
 * Drive one motor.
 * @param pwmPin  PWM output pin
 * @param dirPin  Direction output pin
 * @param value   Signed PWM value [-255, 255]
 */
static void motorSet(uint8_t pwmPin, uint8_t dirPin, int value) {
    if (value >= 0) {
        digitalWrite(dirPin, HIGH);
        analogWrite(pwmPin, (uint8_t)min(value, 255));
    } else {
        digitalWrite(dirPin, LOW);
        analogWrite(pwmPin, (uint8_t)min(-value, 255));
    }
}

/** Brake a motor (both H-bridge inputs high). */
static void motorBrake(uint8_t pwmPin, uint8_t dirPin) {
    digitalWrite(dirPin, HIGH);
    analogWrite(pwmPin, 255);
}

/** Stop a motor (coast). */
static void motorStop(uint8_t pwmPin, uint8_t dirPin) {
    digitalWrite(dirPin, LOW);
    analogWrite(pwmPin, 0);
}

// ===========================================================================
// PID controller
// ===========================================================================

/**
 * Compute PID output.
 * @param target   Target speed (mm/s)
 * @param actual   Actual speed (mm/s)
 * @param state    Per-motor integrator/derivative state
 * @param dt_s     Time step (seconds)
 * @return Signed PWM value in range [-255, 255]
 */
static int computePID(float target, float actual, PidState &state, float dt_s) {
    float error = target - actual;

    state.integral   += error * dt_s;
    state.integral    = constrain(state.integral, -500.0f, 500.0f);  // anti-windup

    float derivative = (dt_s > 0.0f) ? (error - state.prev_error) / dt_s : 0.0f;
    state.prev_error  = error;

    float output = Kp * error + Ki * state.integral + Kd * derivative;
    return (int)constrain(output, -255.0f, 255.0f);
}

// ===========================================================================
// CAN TX helpers
// ===========================================================================

/**
 * Pack a 32-bit signed integer as big-endian into a buffer.
 */
static void pack_int32_be(uint8_t *buf, int32_t val) {
    buf[0] = (uint8_t)((val >> 24) & 0xFF);
    buf[1] = (uint8_t)((val >> 16) & 0xFF);
    buf[2] = (uint8_t)((val >>  8) & 0xFF);
    buf[3] = (uint8_t)( val        & 0xFF);
}

/**
 * Pack a 16-bit signed integer as big-endian into a buffer.
 */
static void pack_int16_be(uint8_t *buf, int16_t val) {
    buf[0] = (uint8_t)((val >> 8) & 0xFF);
    buf[1] = (uint8_t)( val       & 0xFF);
}

/** Send encoder counts on CAN 0x220. */
static void sendEncoderFrame() {
    uint8_t data[8] = {0};
    noInterrupts();
    long el = g_enc_l_count;
    long er = g_enc_r_count;
    interrupts();

    pack_int32_be(&data[0], (int32_t)el);
    pack_int32_be(&data[4], (int32_t)er);

    CAN.sendMsgBuf(CAN_ID_TX_ENC, 0, 8, data);
}

/** Send RPM on CAN 0x320. */
static void sendRpmFrame(int16_t rpmL, int16_t rpmR, uint8_t status) {
    uint8_t data[5] = {0};
    pack_int16_be(&data[0], rpmL);
    pack_int16_be(&data[2], rpmR);
    data[4] = status;

    CAN.sendMsgBuf(CAN_ID_TX_RPM, 0, 5, data);
}

// ===========================================================================
// CAN RX handler
// ===========================================================================

static void handleCanRx() {
    uint8_t  len  = 0;
    uint8_t  rxBuf[8];
    uint32_t rxId = 0;

    while (CAN.checkReceive() == CAN_MSGAVAIL) {
        CAN.readMsgBuf(&rxId, &len, rxBuf);

        if (rxId == CAN_ID_RX_TBW && len >= 4) {
            int16_t  speed   = (int16_t)((rxBuf[0] << 8) | rxBuf[1]);
            uint8_t  brake   = rxBuf[2];
            uint8_t  mode    = rxBuf[3];

            noInterrupts();
            g_speed_mms   = speed;
            g_brake_pct   = brake;
            g_tbw_mode    = mode;
            g_last_rx_ms  = millis();
            interrupts();
        }
    }
}

// ===========================================================================
// setup()
// ===========================================================================

void setup() {
    Serial.begin(115200);
    Serial.println(F("TBW ECU booting..."));

    // Motor pins
    pinMode(MOT_L_PWM, OUTPUT);
    pinMode(MOT_L_DIR, OUTPUT);
    pinMode(MOT_R_PWM, OUTPUT);
    pinMode(MOT_R_DIR, OUTPUT);
    motorStop(MOT_L_PWM, MOT_L_DIR);
    motorStop(MOT_R_PWM, MOT_R_DIR);

    // Encoder pins (input with pull-up)
    pinMode(ENC_L_A, INPUT_PULLUP);
    pinMode(ENC_L_B, INPUT_PULLUP);
    pinMode(ENC_R_A, INPUT_PULLUP);
    pinMode(ENC_R_B, INPUT_PULLUP);

    // Enable PCINT1 for PC0 (A0) and PC2 (A2)
    PCICR  |= _BV(PCIE1);              // enable PCINT[14:8]
    PCMSK1 |= _BV(PCINT8) | _BV(PCINT10);  // A0 and A2

    // CAN INT pin
    pinMode(CAN_INT, INPUT);
    attachInterrupt(digitalPinToInterrupt(CAN_INT), canRxISR, FALLING);

    // Initialise MCP2515
    while (CAN.begin(MCP_ANY, CAN_500KBPS, MCP_8MHZ) != CAN_OK) {
        Serial.println(F("CAN init failed — retrying..."));
        delay(500);
    }
    CAN.setMode(MCP_NORMAL);
    Serial.println(F("CAN init OK"));

    // Timing baseline
    uint32_t now    = millis();
    g_last_pid_ms   = now;
    g_last_enc_ms   = now;
    g_last_rpm_ms   = now;
    g_last_rx_ms    = now;   // suppress immediate watchdog

    Serial.println(F("TBW ECU ready."));
}

// ===========================================================================
// loop()
// ===========================================================================

void loop() {
    uint32_t now = millis();

    // ── Service CAN RX ──────────────────────────────────────────────────────
    if (g_can_rx_flag) {
        g_can_rx_flag = false;
        handleCanRx();
    }

    // ── Watchdog ────────────────────────────────────────────────────────────
    noInterrupts();
    uint32_t last_rx = g_last_rx_ms;
    interrupts();

    if ((now - last_rx) > WATCHDOG_MS) {
        noInterrupts();
        g_tbw_mode  = MODE_IDLE;
        g_speed_mms = 0;
        interrupts();
    }

    // ── PID / Motor control at 50 Hz ────────────────────────────────────────
    if ((now - g_last_pid_ms) >= PID_RATE_MS) {
        float dt_s = (float)(now - g_last_pid_ms) / 1000.0f;
        g_last_pid_ms = now;

        noInterrupts();
        uint8_t  mode    = g_tbw_mode;
        int16_t  target  = g_speed_mms;
        interrupts();

        if (mode == MODE_ESTOP) {
            // Hard brake both motors
            motorBrake(MOT_L_PWM, MOT_L_DIR);
            motorBrake(MOT_R_PWM, MOT_R_DIR);
            // Reset PID integrators
            g_pid_l.integral = g_pid_r.integral = 0.0f;

        } else if (mode == MODE_RC) {
            // Compute actual speed from encoder delta
            noInterrupts();
            long el = g_enc_l_count;
            long er = g_enc_r_count;
            interrupts();

            long delta_l = el - g_enc_l_prev_pid;
            long delta_r = er - g_enc_r_prev_pid;
            g_enc_l_prev_pid = el;
            g_enc_r_prev_pid = er;

            // ticks / dt_s → ticks per second.
            // 1 tick ≈ (wheel circumference / TICKS_PER_REV) mm
            // For speed_mms: actual_mms = (delta / dt_s) * (circumference_mm / TICKS_PER_REV)
            // We treat the raw tick rate as proportional to speed_mms for PID purposes.
            // Calibrate Kp accordingly for the actual wheel.
            float actual_l = (float)delta_l / dt_s;   // ticks/s
            float actual_r = (float)delta_r / dt_s;

            // Target in ticks/s (approximate — calibrate to hardware)
            float target_tps = (float)target;   // 1 mm/s ≈ 1 tick/s placeholder

            int pwm_l = computePID(target_tps, actual_l, g_pid_l, dt_s);
            int pwm_r = computePID(target_tps, actual_r, g_pid_r, dt_s);

            motorSet(MOT_L_PWM, MOT_L_DIR, pwm_l);
            motorSet(MOT_R_PWM, MOT_R_DIR, pwm_r);

        } else {
            // MODE_IDLE
            motorStop(MOT_L_PWM, MOT_L_DIR);
            motorStop(MOT_R_PWM, MOT_R_DIR);
            g_pid_l.integral = g_pid_r.integral = 0.0f;
        }
    }

    // ── Encoder TX at 20 Hz ─────────────────────────────────────────────────
    if ((now - g_last_enc_ms) >= ENC_TX_MS) {
        g_last_enc_ms = now;
        sendEncoderFrame();
    }

    // ── RPM TX at 10 Hz ─────────────────────────────────────────────────────
    if ((now - g_last_rpm_ms) >= RPM_TX_MS) {
        uint32_t elapsed = now - g_last_rpm_ms;
        g_last_rpm_ms = now;

        noInterrupts();
        long el = g_enc_l_count;
        long er = g_enc_r_count;
        interrupts();

        long delta_l = el - g_enc_l_prev_rpm;
        long delta_r = er - g_enc_r_prev_rpm;
        g_enc_l_prev_rpm = el;
        g_enc_r_prev_rpm = er;

        // RPM = (ticks per elapsed_ms) * 1000 * 60 / (ticks_per_rev * elapsed_ms)
        //     = delta * 60000 / (TICKS_PER_REV * elapsed)
        // Using integer arithmetic; guard against divide-by-zero.
        int16_t rpmL = 0;
        int16_t rpmR = 0;
        if (elapsed > 0) {
            rpmL = (int16_t)((long)delta_l * 60000L / ((long)TICKS_PER_REV * (long)elapsed));
            rpmR = (int16_t)((long)delta_r * 60000L / ((long)TICKS_PER_REV * (long)elapsed));
        }

        noInterrupts();
        uint8_t mode_snap = g_tbw_mode;
        interrupts();
        uint8_t status = (mode_snap == MODE_ESTOP) ? 2 : (mode_snap == MODE_RC ? 1 : 0);

        sendRpmFrame(rpmL, rpmR, status);
    }
}
