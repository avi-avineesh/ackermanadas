/*
 * sbw_ecu.ino — Steer-By-Wire ECU Firmware
 * Target  : Arduino Uno
 * Crystal : 8 MHz
 * CAN     : MCP2515 via MCP_CAN (Cory J. Fowler), 500 kbps
 *
 * CAN RX  0x110 : steer_mrad int16 BE (bytes 0-1), range ±700 mrad
 *                 → maps to servo pulse [1000, 2000] µs
 *                   pulse_us = 1500 + (steer_mrad * 500L) / 700
 *
 * CAN TX  0x310 at 10 Hz:
 *   actual_mrad int16 BE (bytes 0-1) = last commanded steer_mrad
 *   status      uint8   (byte  2)    : 0=ok, 1=watchdog_center, 2=limit_clamp
 *
 * Watchdog: if no 0x110 in 500 ms → centre servo (1500 µs), status=1
 *
 * Pins
 *   SERVO_PIN = 9  (D9, Servo PWM)
 *   CAN_CS    = 10 (D10)
 *   CAN_INT   = 2  (D2, INT0)
 */

#include <SPI.h>
#include <mcp_can.h>
#include <Servo.h>

// ---------------------------------------------------------------------------
// Pin definitions
// ---------------------------------------------------------------------------
#define SERVO_PIN  9
#define CAN_CS     10
#define CAN_INT    2

// ---------------------------------------------------------------------------
// CAN IDs
// ---------------------------------------------------------------------------
#define CAN_ID_RX_SBW    0x110
#define CAN_ID_TX_SBW_FB 0x310

// ---------------------------------------------------------------------------
// Servo / steer constants
// ---------------------------------------------------------------------------
#define STEER_MRAD_MAX   700      // ±700 mrad hardware limit
#define SERVO_CENTRE_US  1500     // neutral pulse width
#define SERVO_MIN_US     1000     // full-left pulse
#define SERVO_MAX_US     2000     // full-right pulse

// ---------------------------------------------------------------------------
// Timing
// ---------------------------------------------------------------------------
#define WATCHDOG_MS   500         // no CAN → centre after 500 ms
#define FB_TX_MS      100         // feedback TX every 100 ms → 10 Hz

// ---------------------------------------------------------------------------
// Status byte values
// ---------------------------------------------------------------------------
#define STATUS_OK              0
#define STATUS_WATCHDOG_CENTER 1
#define STATUS_LIMIT_CLAMP     2

// ---------------------------------------------------------------------------
// Global objects
// ---------------------------------------------------------------------------
MCP_CAN CAN(CAN_CS);
Servo   g_servo;

// ---------------------------------------------------------------------------
// Shared state
// ---------------------------------------------------------------------------
volatile int16_t  g_steer_mrad   = 0;       // last commanded mrad (from CAN)
volatile uint32_t g_last_rx_ms   = 0;       // millis() of last 0x110 frame

// Feedback state (set in main loop, read for TX)
int16_t  g_actual_mrad = 0;
uint8_t  g_status      = STATUS_OK;

// Timing
uint32_t g_last_fb_ms = 0;

// CAN interrupt flag
volatile bool g_can_rx_flag = false;

// ===========================================================================
// ISRs
// ===========================================================================

/** INT0 — MCP2515 data-ready interrupt (active-low). */
void canRxISR() {
    g_can_rx_flag = true;
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

        if (rxId == CAN_ID_RX_SBW && len >= 2) {
            int16_t mrad = (int16_t)((rxBuf[0] << 8) | rxBuf[1]);

            noInterrupts();
            g_steer_mrad  = mrad;
            g_last_rx_ms  = millis();
            interrupts();
        }
    }
}

// ===========================================================================
// Servo helpers
// ===========================================================================

/**
 * Convert steer_mrad to a servo pulse width in microseconds.
 * Mapping: ±700 mrad → 1000–2000 µs  (centre = 1500 µs)
 *
 * pulse_us = 1500 + (steer_mrad * 500L) / 700
 *
 * @param mrad   Steering demand in mrad (will be clamped internally)
 * @param[out] clamped  Set to true if mrad was out of ±700 range
 * @return Pulse width in µs [1000, 2000]
 */
static int16_t mradToPulse(int16_t mrad, bool &clamped) {
    clamped = false;

    if (mrad >  STEER_MRAD_MAX) { mrad =  STEER_MRAD_MAX; clamped = true; }
    if (mrad < -STEER_MRAD_MAX) { mrad = -STEER_MRAD_MAX; clamped = true; }

    int16_t pulse = (int16_t)(SERVO_CENTRE_US + ((int32_t)mrad * 500L) / 700L);

    // Clamp for safety (should be redundant after mrad clamp, but be explicit)
    if (pulse < SERVO_MIN_US) { pulse = SERVO_MIN_US; clamped = true; }
    if (pulse > SERVO_MAX_US) { pulse = SERVO_MAX_US; clamped = true; }

    return pulse;
}

// ===========================================================================
// CAN TX helper
// ===========================================================================

static void sendFeedbackFrame(int16_t actual_mrad, uint8_t status) {
    uint8_t data[3];
    data[0] = (uint8_t)((actual_mrad >> 8) & 0xFF);
    data[1] = (uint8_t)( actual_mrad       & 0xFF);
    data[2] = status;

    CAN.sendMsgBuf(CAN_ID_TX_SBW_FB, 0, 3, data);
}

// ===========================================================================
// setup()
// ===========================================================================

void setup() {
    Serial.begin(115200);
    Serial.println(F("SBW ECU booting..."));

    // Attach servo and centre it
    g_servo.attach(SERVO_PIN, SERVO_MIN_US, SERVO_MAX_US);
    g_servo.writeMicroseconds(SERVO_CENTRE_US);

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

    // Timing baseline — suppress immediate watchdog
    uint32_t now  = millis();
    g_last_rx_ms  = now;
    g_last_fb_ms  = now;

    Serial.println(F("SBW ECU ready."));
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

    // ── Watchdog + servo update ─────────────────────────────────────────────
    noInterrupts();
    uint32_t last_rx   = g_last_rx_ms;
    int16_t  cmd_mrad  = g_steer_mrad;
    interrupts();

    if ((now - last_rx) > WATCHDOG_MS) {
        // Watchdog expired — centre the steering
        g_servo.writeMicroseconds(SERVO_CENTRE_US);
        g_actual_mrad = 0;
        g_status      = STATUS_WATCHDOG_CENTER;
    } else {
        // Normal operation — apply commanded steer
        bool clamped = false;
        int16_t pulse = mradToPulse(cmd_mrad, clamped);
        g_servo.writeMicroseconds(pulse);
        g_actual_mrad = cmd_mrad;   // report commanded value as actual (no position sensor)
        g_status      = clamped ? STATUS_LIMIT_CLAMP : STATUS_OK;
    }

    // ── Feedback TX at 10 Hz ────────────────────────────────────────────────
    if ((now - g_last_fb_ms) >= FB_TX_MS) {
        g_last_fb_ms = now;
        sendFeedbackFrame(g_actual_mrad, g_status);
    }
}
