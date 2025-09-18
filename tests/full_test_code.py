from machine import Pin, PWM, ADC
import time

# -------------------
# Pin configuration
# -------------------
BUZZER_PIN = 15        # GP16 → buzzer +
LDR_PIN = 28           # GP28 → photoresistor divider output (ADC2)

# Assign your RGB LED pins (update if wired differently)
RED_PIN = 1
GREEN_PIN = 2
BLUE_PIN = 3

# -------------------
# Initialize hardware
# -------------------
buzzer = PWM(Pin(BUZZER_PIN))
ldr = ADC(Pin(LDR_PIN))

led_red = Pin(RED_PIN, Pin.OUT)
led_green = Pin(GREEN_PIN, Pin.OUT)
led_blue = Pin(BLUE_PIN, Pin.OUT)

# -------------------
# Helper functions
# -------------------
def beep(freq=440, duration_ms=200, duty=0.5):
    """Play a tone at given frequency and duration."""
    buzzer.duty_u16(int(65535 * duty))
    buzzer.freq(int(freq))
    time.sleep_ms(duration_ms)
    buzzer.duty_u16(0)

def read_light():
    """Return normalized light level [0.0 .. 1.0]."""
    raw = ldr.read_u16()  # 0–65535
    return raw / 65535.0

def set_rgb(r, g, b):
    """Turn RGB LED on/off (digital control)."""
    led_red.value(1 if r else 0)
    led_green.value(1 if g else 0)
    led_blue.value(1 if b else 0)

# -------------------
# Test routine
# -------------------
print("Starting RGB + buzzer + LDR test...")

# 1. RGB LED test
print("Cycling through colors...")
set_rgb(1,0,0); time.sleep(0.5)   # Red
set_rgb(0,1,0); time.sleep(0.5)   # Green
set_rgb(0,0,1); time.sleep(0.5)   # Blue
set_rgb(1,1,0); time.sleep(0.5)   # Yellow
set_rgb(0,1,1); time.sleep(0.5)   # Cyan
set_rgb(1,0,1); time.sleep(0.5)   # Magenta
set_rgb(1,1,1); time.sleep(0.5)   # White
set_rgb(0,0,0)                    # Off

# 2. Buzzer test
print("Buzzer: 3 beeps (low, mid, high)")
beep(220, 300)
beep(440, 300)
beep(880, 300)

# 3. LDR interactive test
print("Cover/uncover the photoresistor. Ctrl+C to stop.")
try:
    while True:
        light_level = read_light()   # 0.0 = dark, 1.0 = bright
        print("Light level:", round(light_level, 2))

        # LED color changes with light level
        if light_level < 0.5:
            set_rgb(1,0,0)   # Dark → Red
        elif light_level < 0.8:
            set_rgb(0,1,0)   # Medium → Green
        else:
            set_rgb(0,0,1)   # Bright → Blue

        # Buzzer pitch follows light
        freq = 200 + int(1800 * light_level)  # 200 Hz .. 2000 Hz
        duty = 0.3 if light_level > 0.1 else 0.0
        if duty > 0:
            buzzer.duty_u16(int(65535 * duty))
            buzzer.freq(freq)
        else:
            buzzer.duty_u16(0)

        time.sleep(0.2)

except KeyboardInterrupt:
    print("Test stopped by user.")
    buzzer.deinit()
    set_rgb(0,0,0)
