"""
PWMAudio — minimal PWM tone driver (Pico 2WH, GP16 by default).

Public API (MVP):
    play_tone(freq_hz: float, duration_ms: int, volume: float = TONE_DUTY) -> None

Notes:
- Uses pin/bounds from config.pins (no hard-coding).
- Importing on a laptop is fine; instantiating requires MicroPython.
- Pop-safe order: duty→0, set freq, set duty, sleep, duty→0.
"""

from config.pins import PIN_BUZZER, TONE_DUTY, MIN_TONE_HZ, MAX_TONE_HZ
""" 
pulls pin and tunables from central config (pins.py)
tries to import machine.pin/machin.pwm
if available, =True
if not, =False
"""
try:
    from machine import Pin, PWM
    import time
    _MICROPY = True
except Exception:
    Pin = PWM = None
    import time
    _MICROPY = False



class PWMAudio:
    def __init__(self, pin_num: int = PIN_BUZZER):
        """ 
        uses the configured buzzer pin from pins.py
        prevents misuse on a laptop, importing is fine but constructing the driver
        without hardware raises a clear error
        initializes pwm and mutes immediately so there's no startup click/pop
        """
        if not _MICROPY:
            raise RuntimeError("PWMAudio requires MicroPython on the Pico (machine.PWM).")
        self._pwm = PWM(Pin(pin_num))
        self._pwm.duty_u16(0)  # ensure silent on init


    def play_tone(self, freq_hz: float, duration_ms: int, volume: float = TONE_DUTY) -> None:
        """
        Play a simple square-wave tone, then stop (blocking).
        guards against invalid inputs, non positive frequency/duration = no-op
        clamps volume 
        clamps frequency to safe pwm band from pins.py
        """
        if freq_hz <= 0 or duration_ms <= 0:
            return
        
        # clamp inputs
        volume = max(0.0, min(1.0, float(volume)))
        f = max(MIN_TONE_HZ, min(MAX_TONE_HZ, float(freq_hz)))

        #sets duty to 0 first, then sets frequency, then raises duty
        #order avoids audible pops/clicks when changing frequency
        # pop-safe order
        self._pwm.duty_u16(0)
        self._pwm.freq(int(f))
        self._pwm.duty_u16(int(65535 * volume))

        #blocks for the request duration
        #returns to silent so no "stuck tone" between notes
        time.sleep_ms(int(duration_ms))
        self._pwm.duty_u16(0)  # stop cleanly
