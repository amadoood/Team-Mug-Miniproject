"""
pins.py — central config for pins and HAL tunables.
- Single source of truth for wiring and 'knobs' (no `machine` imports here).
- If wiring changes, update values here — not in drivers.
"""

# === Execution mode (app can override for laptop simulation) ===
SIMULATION = False  # True → use fake drivers on laptop; False → Pico hardware

# === Pin map (Raspberry Pi Pico 2WH) ===
PIN_LDR_ADC = 28     # GP28 (ADC2) — light sensor
PIN_BUZZER  = 16     # GP16 (PWM)  — piezo buzzer
PIN_BTN_A   = 14     # GP14 (pull-up) — button A
PIN_BTN_B   = 15     # GP15 (pull-up) — button B



# === ADC tuning (used by hal/adc_reader.py) ===
# Trade-offs:
# - ADC_SAMPLES: more samples → less noise, more CPU
# - EMA_ALPHA  : lower → smoother but slower response
# - MEDIAN_WIN : 3 enables a small spike-killing median; 1 disables
ADC_SAMPLES = 4
EMA_ALPHA   = 0.30
MEDIAN_WIN  = 1



# Two-point calibration placeholders (raw 16-bit ADC range 0..65535)
# You can overwrite these later from a calibration script (dark / bright).
RAW_DARK_DEFAULT   = 0
RAW_BRIGHT_DEFAULT = 65535


# === Buttons (used by hal/gpio_ui.py later) ===
BTN_DEBOUNCE_MS = 30   # basic software debounce


# === Loop timing target (used by app/orchestrator) ===
LOOP_PERIOD_MS = 10    # control loop tick; ties to CPU < 25% goal


# === Audio defaults/bounds (used by hal/pwm_audio.py & audio layers) ===
TONE_DUTY   = 0.50     # 0..1 perceived loudness (stay ≤ 0.7 to avoid harshness)
MIN_TONE_HZ = 20.0     # clamp very low pitches (below typical PWM audio range)
MAX_TONE_HZ = 10000.0  # clamp very high pitches
