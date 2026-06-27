/*
 * combined_ecu.ino — Combined TBW + SBW ECU Firmware
 * Target  : Arduino Uno (single board replaces former tbw_ecu + sbw_ecu)
 * CAN     : MCP2515 via MCP_CAN (Cory J. Fowler), 500 kbps, 8 MHz crystal
 *
 * ── CAN RX ──────────────────────────────────────────────────────────────────
 *   0x110  steer_mrad   int16 BE  bytes 0-1   ±2500 mrad → servo angle
 *   0x120  speed_mms    int16 BE  bytes 0-1   ±500 mm/s
 *          brake_pct    uint8     byte  2     0-100 %
 *          mode         uint8     byte  3     0=IDLE  1=AUTO  2=ESTOP
 *
 * ── CAN TX ──────────────────────────────────────────────────────────────────
 *   0x320 @ 10 Hz (every 100 ms)
 *          status       uint8     byte  0     0=IDLE 1=RUNNING 2=ESTOP
 *          hb_counter   uint8     byte  1     wraps 0-255
 *
 * ── Servo mapping ───────────────────────────────────────────────────────────
 *   deg = SERVO_CENTRE + (steer_mrad / STEER_MAX_MRAD) * SERVO_GAIN
 *   SERVO_CENTRE = 90 deg,  SERVO_GAIN = 43.0,  STEER_MAX_MRAD = 2500
 *   Range: [47, 133] degrees
 *
 * ── Speed → PWM mapping ─────────────────────────────────────────────────────
 *   |speed_mms|  0        →  PWM 0
 *   |speed_mms|  1-500    →  PWM clamp(raw, PWM_MIN, PWM_MAX)
 *   raw = |speed_mms| * PWM_MAX / SPEED_MAX_MMS
 *   PWM_MIN = 60,  PWM_MAX = 150
 *
 * ── Motor balance ───────────────────────────────────────────────────────────
 *   Left motor runs faster → scale left PWM by LEFT_BALANCE = 0.62
 *
 * ── Watchdog ────────────────────────────────────────────────────────────────
 *   No 0x120 for 500 ms → stop motors + centre servo → mode = IDLE
 *
 * ── Pins ────────────────────────────────────────────────────────────────────
 *   D4  MOT_L_DIR    D5  MOT_L_PWM
 *   D6  MOT_R_PWM    D7  MOT_R_DIR
 *   D9  SERVO_PIN
 *   D10 CAN_CS   D11 MOSI   D12 MISO   D13 SCK   D2 CAN_INT
 */

#include <SPI.h>
#include <mcp_can.h>
#include <Servo.h>

// ── Pin definitions ──────────────────────────────────────────────────────────
#define MOT_L_DIR   4
#define MOT_L_PWM   5
#define MOT_R_PWM   6
#define MOT_R_DIR   7
#define SERVO_PIN   9
#define CAN_CS      10
#define CAN_INT     2

// ── CAN IDs ──────────────────────────────────────────────────────────────────
#define CAN_ID_RX_STEER   0x110
#define CAN_ID_RX_DRIVE   0x120
#define CAN_ID_TX_STATUS  0x320

// ── Speed → PWM constants ────────────────────────────────────────────────────
#define SPEED_MAX_MMS   500
#define PWM_MAX         150
#define PWM_MIN          60
static const float LEFT_BALANCE = 0.62f;   // reduce left motor (runs faster)

// ── Servo constants ──────────────────────────────────────────────────────────
#define SERVO_CENTRE     90          // neutral angle (degrees)
static const float SERVO_GAIN     = 43.0f;
static const float STEER_MAX_MRAD = 2500.0f;
#define SERVO_DEG_MIN    47          // = CENTRE - GAIN
#define SERVO_DEG_MAX   133          // = CENTRE + GAIN

// ── Mode constants ───────────────────────────────────────────────────────────
#define MODE_IDLE   0
#define MODE_AUTO   1
#define MODE_ESTOP  2

// ── Status byte (0x320) ──────────────────────────────────────────────────────
#define STATUS_IDLE    0
#define STATUS_RUNNING 1
#define STATUS_ESTOP   2

// ── Timing (ms) ──────────────────────────────────────────────────────────────
#define WATCHDOG_MS   500u   // 0x120 silence → stop
#define HB_TX_MS      100u   // 0x320 heartbeat period  (10 Hz)
#define DEBUG_MS      500u   // serial debug period

// ────────────────────────────────────────────────────────────────────────────
// Global objects
// ────────────────────────────────────────────────────────────────────────────
MCP_CAN CAN(CAN_CS);
Servo   g_servo;

// ────────────────────────────────────────────────────────────────────────────
// Command state  (written by CAN RX, read by main loop)
// Protect multi-byte fields with noInterrupts()/interrupts().
// ────────────────────────────────────────────────────────────────────────────
volatile int16_t  g_steer_mrad  = 0;
volatile int16_t  g_speed_mms   = 0;
volatile uint8_t  g_brake_pct   = 0;
volatile uint8_t  g_mode        = MODE_IDLE;
volatile uint32_t g_last_120_ms = 0;    // millis() of last valid 0x120

// ────────────────────────────────────────────────────────────────────────────
// Heartbeat state
// ────────────────────────────────────────────────────────────────────────────
static uint8_t  g_hb_counter = 0;

// ────────────────────────────────────────────────────────────────────────────
// Timing
// ────────────────────────────────────────────────────────────────────────────
static uint32_t g_last_hb_ms    = 0;
static uint32_t g_last_debug_ms = 0;

// ────────────────────────────────────────────────────────────────────────────
// CAN interrupt flag (set by INT0 ISR, consumed in loop)
// ────────────────────────────────────────────────────────────────────────────
volatile bool g_can_rx_flag = false;

// ============================================================================
// ISR
// ============================================================================

void canRxISR() {
    g_can_rx_flag = true;
}

// ============================================================================
// Motor helpers  (SmartElex 10D dual H-bridge)
// ============================================================================

/** Drive one motor side with a signed PWM value [-255, 255]. */
static void motorSet(uint8_t pwmPin, uint8_t dirPin, int value) {
    if (value >= 0) {
        digitalWrite(dirPin, HIGH);
        analogWrite(pwmPin, (uint8_t)min(value, 255));
    } else {
        digitalWrite(dirPin, LOW);
        analogWrite(pwmPin, (uint8_t)min(-value, 255));
    }
}

/** Regenerative brake: both H-bridge inputs high. */
static void motorBrake(uint8_t pwmPin, uint8_t dirPin) {
    digitalWrite(dirPin, HIGH);
    analogWrite(pwmPin, 255);
}

/** Coast stop. */
static void motorCoast(uint8_t pwmPin, uint8_t dirPin) {
    digitalWrite(dirPin, LOW);
    analogWrite(pwmPin, 0);
}

/** Stop both motors (coast). */
static void motorsStop() {
    motorCoast(MOT_L_PWM, MOT_L_DIR);
    motorCoast(MOT_R_PWM, MOT_R_DIR);
}

/** Brake both motors. */
static void motorsBrake() {
    motorBrake(MOT_L_PWM, MOT_L_DIR);
    motorBrake(MOT_R_PWM, MOT_R_DIR);
}

// ============================================================================
// Speed → PWM mapping
// ============================================================================

/**
 * Map |speed_mms| to a base PWM value [0, PWM_MAX].
 * Returns 0 for zero speed, otherwise clamps to [PWM_MIN, PWM_MAX].
 */
static uint8_t speedToPwm(int16_t speed_mms) {
    if (speed_mms == 0) return 0;
    int32_t raw = ((int32_t)abs(speed_mms) * (int32_t)PWM_MAX) / SPEED_MAX_MMS;
    if (raw < PWM_MIN) raw = PWM_MIN;
    if (raw > PWM_MAX) raw = PWM_MAX;
    return (uint8_t)raw;
}

// ============================================================================
// Servo helpers
// ============================================================================

/** Clamp an integer angle to valid servo range. */
static int clampDeg(int deg) {
    if (deg < SERVO_DEG_MIN) return SERVO_DEG_MIN;
    if (deg > SERVO_DEG_MAX) return SERVO_DEG_MAX;
    return deg;
}

/**
 * Convert steering demand in mrad to servo degrees and write.
 *   deg = SERVO_CENTRE + (steer_mrad / STEER_MAX_MRAD) * SERVO_GAIN
 */
static void applySteer(int16_t mrad) {
    float deg_f = (float)SERVO_CENTRE
                  + ((float)mrad / STEER_MAX_MRAD) * SERVO_GAIN;
    g_servo.write(clampDeg((int)deg_f));
}

/** Centre the servo. */
static void servoCenter() {
    g_servo.write(SERVO_CENTRE);
}

// ============================================================================
// CAN helpers
// ============================================================================

/**
 * Drain the MCP2515 RX buffer and update global command state.
 * Called from loop() after g_can_rx_flag is set.
 */
static void handleCanRx() {
    uint8_t  len   = 0;
    uint8_t  rxBuf[8];
    uint32_t rxId  = 0;

    while (CAN.checkReceive() == CAN_MSGAVAIL) {
        CAN.readMsgBuf(&rxId, &len, rxBuf);

        if (rxId == CAN_ID_RX_STEER && len >= 2) {
            int16_t mrad = (int16_t)(((uint16_t)rxBuf[0] << 8) | rxBuf[1]);
            noInterrupts();
            g_steer_mrad = mrad;
            interrupts();
        }
        else if (rxId == CAN_ID_RX_DRIVE && len >= 4) {
            int16_t speed = (int16_t)(((uint16_t)rxBuf[0] << 8) | rxBuf[1]);
            uint8_t brake = rxBuf[2];
            uint8_t mode  = rxBuf[3];
            noInterrupts();
            g_speed_mms  = speed;
            g_brake_pct  = brake;
            g_mode       = mode;
            g_last_120_ms = millis();
            interrupts();
        }
    }
}

/** Send 0x320 heartbeat frame. */
static void sendHeartbeat(uint8_t status) {
    uint8_t data[2];
    data[0] = status;
    data[1] = g_hb_counter++;          // wraps 0→255→0
    CAN.sendMsgBuf(CAN_ID_TX_STATUS, 0, 2, data);
}

// ============================================================================
// setup()
// ============================================================================

void setup() {
    Serial.begin(115200);
    Serial.println(F("combined_ecu booting..."));

    // ── Motor pins ────────────────────────────────────────────────────────────
    pinMode(MOT_L_PWM, OUTPUT);
    pinMode(MOT_L_DIR, OUTPUT);
    pinMode(MOT_R_PWM, OUTPUT);
    pinMode(MOT_R_DIR, OUTPUT);
    motorsStop();
    Serial.println(F("Motors initialised"));

    // ── Servo ─────────────────────────────────────────────────────────────────
    g_servo.attach(SERVO_PIN);
    servoCenter();
    Serial.println(F("Servo centred"));

    // ── CAN INT pin ───────────────────────────────────────────────────────────
    pinMode(CAN_INT, INPUT);
    attachInterrupt(digitalPinToInterrupt(CAN_INT), canRxISR, FALLING);

    // ── MCP2515 init (retry until success) ───────────────────────────────────
    Serial.println(F("Initialising MCP2515..."));
    while (CAN.begin(MCP_ANY, CAN_500KBPS, MCP_8MHZ) != CAN_OK) {
        Serial.println(F("  CAN init failed — retrying in 500 ms"));
        delay(500);
    }
    CAN.setMode(MCP_NORMAL);
    Serial.println(F("CAN init OK"));

    // ── Timing baseline (suppress immediate watchdog) ─────────────────────────
    uint32_t now    = millis();
    g_last_120_ms   = now;
    g_last_hb_ms    = now;
    g_last_debug_ms = now;

    Serial.println(F("combined_ecu ready."));
    Serial.println(F("  CAN RX: 0x110 (steer) | 0x120 (drive)"));
    Serial.println(F("  CAN TX: 0x320 (status/heartbeat @ 10 Hz)"));
}

// ============================================================================
// loop()
// ============================================================================

void loop() {
    uint32_t now = millis();

    // ── Service CAN RX ────────────────────────────────────────────────────────
    if (g_can_rx_flag) {
        g_can_rx_flag = false;
        handleCanRx();
    }

    // ── Snapshot volatile state ───────────────────────────────────────────────
    noInterrupts();
    int16_t  speed     = g_speed_mms;
    int16_t  steer     = g_steer_mrad;
    uint8_t  brake     = g_brake_pct;
    uint8_t  mode      = g_mode;
    uint32_t last_120  = g_last_120_ms;
    interrupts();

    // ── Watchdog: no 0x120 for WATCHDOG_MS → safe stop ───────────────────────
    if ((now - last_120) > WATCHDOG_MS) {
        if (mode != MODE_IDLE) {
            Serial.println(F("WD: 0x120 timeout — stopping"));
        }
        noInterrupts();
        g_mode      = MODE_IDLE;
        g_speed_mms = 0;
        interrupts();
        mode  = MODE_IDLE;
        speed = 0;
    }

    // ── Actuator update ───────────────────────────────────────────────────────
    if (mode == MODE_ESTOP) {
        // Hard brake; do NOT centre servo (retain last steer — car may be
        // stopping mid-corner and braking is the priority)
        motorsBrake();
    }
    else if (mode == MODE_AUTO) {
        // Steer
        applySteer(steer);

        // Drive — apply LEFT_BALANCE to compensate for left-motor speed bias
        uint8_t base_pwm = speedToPwm(speed);
        uint8_t left_pwm = (uint8_t)((float)base_pwm * LEFT_BALANCE);
        // Enforce minimum threshold on the balanced side too
        if (left_pwm > 0 && left_pwm < PWM_MIN) left_pwm = PWM_MIN;

        if (speed > 0) {
            motorSet(MOT_L_PWM, MOT_L_DIR,  (int)left_pwm);
            motorSet(MOT_R_PWM, MOT_R_DIR,  (int)base_pwm);
        } else if (speed < 0) {
            motorSet(MOT_L_PWM, MOT_L_DIR, -(int)left_pwm);
            motorSet(MOT_R_PWM, MOT_R_DIR, -(int)base_pwm);
        } else {
            // speed == 0: brake if brake_pct > 0, else coast
            if (brake > 0) {
                motorsBrake();
            } else {
                motorsStop();
            }
        }
    }
    else {
        // MODE_IDLE: coast stop + centre servo
        motorsStop();
        servoCenter();
    }

    // ── Heartbeat TX at 10 Hz ─────────────────────────────────────────────────
    if ((now - g_last_hb_ms) >= HB_TX_MS) {
        g_last_hb_ms = now;

        uint8_t status;
        switch (mode) {
            case MODE_AUTO:  status = STATUS_RUNNING; break;
            case MODE_ESTOP: status = STATUS_ESTOP;   break;
            default:         status = STATUS_IDLE;    break;
        }
        sendHeartbeat(status);
    }

    // ── Serial debug at 2 Hz ─────────────────────────────────────────────────
    if ((now - g_last_debug_ms) >= DEBUG_MS) {
        g_last_debug_ms = now;

        const char *mode_str =
            (mode == MODE_AUTO)  ? "AUTO"  :
            (mode == MODE_ESTOP) ? "ESTOP" : "IDLE";

        Serial.print(F("mode="));   Serial.print(mode_str);
        Serial.print(F(" spd="));   Serial.print(speed);
        Serial.print(F("mms steer="));Serial.print(steer);
        Serial.print(F("mrad brk=")); Serial.print(brake);
        Serial.print(F("% hb="));   Serial.println(g_hb_counter);
    }
}
