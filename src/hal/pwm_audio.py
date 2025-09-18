# pwm_audio.py
"""
PWMAudio — minimal PWM tone driver (Pico 2WH, GP16 by default).

Public API (MVP):
    play_tone(freq_hz: float, duration_ms: int, volume: float = TONE_DUTY) -> None

Notes:
- Uses pin/bounds from config.pins (no hard-coding).
- Importing on a laptop is fine; instantiating requires MicroPython.
- Pop-safe order: duty→0, set freq, set duty, sleep, duty→0.

NEW (for Synth integration):
- Added non-blocking API: set_freq(), set_duty(), stop().
- Keeps play_tone() intact, now calls into non-blocking functions under the hood.
"""

from config.pins import PIN_BUZZER, TONE_DUTY, MIN_TONE_HZ, MAX_TONE_HZ
"""
pulls pin and tunables from central config (pins.py)
tries to import machine.pin/machine.pwm
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
        self._freq = 0         # NEW: track active frequency
        self._active = False   # NEW: track active state


    # --- NEW Non-blocking API expected by Synth ---
    def set_freq(self, frequency: float) -> None:
        """Set square-wave frequency without blocking (Synth will tick duty)."""
        if frequency is None or frequency <= 0:
            self.stop()
            return
        f = max(MIN_TONE_HZ, min(MAX_TONE_HZ, float(frequency)))
        self._pwm.freq(int(f))
        self._freq = int(f)
        if not self._active:
            self._pwm.duty_u16(0)  # start silent
            self._active = True

    def set_duty(self, duty_cycle_0_1: float) -> None:
        """Set duty (volume) in 0..1 non-blocking."""
        if not self._active:
            return
        d = max(0.0, min(1.0, float(duty_cycle_0_1)))
        self._pwm.duty_u16(int(65535 * d))

    def stop(self) -> None:
        """Silence output (non-blocking)."""
        try:
            self._pwm.duty_u16(0)
        finally:
            self._active = False
            self._freq = 0


    # --- Original blocking API (unchanged interface) ---
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
        self.set_freq(f)       # NEW: reuse non-blocking API
        self.set_duty(volume)  # NEW: reuse non-blocking API

        #blocks for the request duration
        time.sleep_ms(int(duration_ms))
        self.stop()            # NEW: reuse non-blocking API


    # --- NEW optional cleanup ---
    def deinit(self) -> None:
        """Release PWM cleanly (optional)."""
        try:
            self.stop()
            self._pwm.deinit()
        except Exception:
            pass
