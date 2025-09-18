from machine import Pin, PWM
import time

# Adjust this if your buzzer is on a different pin (GP16 is common)
BUZZER_PIN = 15

# Initialize PWM on the buzzer pin
buzzer = PWM(Pin(BUZZER_PIN))

def beep(freq=440, duration_ms=500, duty=0.5):
    """
    Play a tone at given frequency and duration.
    freq: frequency in Hz
    duration_ms: duration in milliseconds
    duty: loudness (0.0–1.0, capped at ~0.5 for passive buzzers)
    """
    buzzer.duty_u16(int(65535 * duty))  # set volume
    buzzer.freq(int(freq))              # set frequency
    time.sleep_ms(duration_ms)
    buzzer.duty_u16(0)                  # mute after beep

# --- Test sequence ---
print("Starting buzzer test...")

# 1. Single beep
beep(440, 500)

# 2. Two short beeps
for _ in range(2):
    beep(880, 200)
    time.sleep_ms(100)

# 3. Simple scale
for f in [262, 294, 330, 349, 392, 440, 494, 523]:
    beep(f, 250)

print("Buzzer test done.")
buzzer.deinit()  # release the pin
