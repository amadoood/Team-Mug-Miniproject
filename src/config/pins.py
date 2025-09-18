"""
pins.py — central config for pins and HAL tunables.
- Single source of truth for wiring and 'knobs' (no `machine` imports here).
- If wiring changes, update values here — not in drivers.
"""

# === Execution mode (app can override for laptop simulation) ===
SIMULATION = False  # True → use fake drivers on laptop; False → Pico hardware

# === Pin map (Raspberry Pi Pico 2WH) ===
PIN_LDR_ADC = 28     # GP28 (ADC2) — light sensor
PIN_BUZZER  = 15     # GP15 (PWM)  — piezo buzzer

PIN_LED_R   = 1     # red led
PIN_LED_G   = 2     # green led
PIN_LED_B   = 3     #blue led

LED_ACTIVE_HIGH = False  #rgb is common-anode   



# === ADC tuning (used by hal/adc_reader.py) ===
# Trade-offs:
# - ADC_SAMPLES: more samples → less noise, more CPU
# - EMA_ALPHA  : lower → smoother but slower response
# - MEDIAN_WIN : 3 enables a small spike-killing median; 1 disables
ADC_SAMPLES = 4
EMA_ALPHA   = 0.30
MEDIAN_WIN  = 1



# Two-point calibration placeholders (raw 16-bit ADC range 0..65535)
# Can overwrite these later from a calibration script (dark / bright).
RAW_DARK_DEFAULT   = 0
RAW_BRIGHT_DEFAULT = 65535


# === Loop timing target (used by app/orchestrator) ===
LOOP_PERIOD_MS = 10    # control loop tick; ties to CPU < 25% goal
BTN_DEBOUNCE_MS = 30   #debounce


# === Audio defaults/bounds (used by hal/pwm_audio.py & audio layers) ===
TONE_DUTY   = 0.50     # 0..1 perceived loudness (stay ≤ 0.7 to avoid harshness)
MIN_TONE_HZ = 20.0     # clamp very low pitches (below typical PWM audio range)
MAX_TONE_HZ = 10000.0  # clamp very high pitches

#backup to avoid breakage
PIN_LDR = PIN_LDR_ADC

