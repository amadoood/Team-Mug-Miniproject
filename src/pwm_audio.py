from config.pins import PIN_BUZZER, SIMULATION
try:
    from machine import Pin, PWM
    _MICROPY = True
except Exception:
    Pin = PWM = None
    _MICROPY = False

class _BasePWM:
    def set_freq(self, hz: float): ...
    def set_duty(self, duty_0_1: float): ...
    def stop(self): ...

class RealPWMDriver(_BasePWM):
    def __init__(self, pin_num: int = PIN_BUZZER):
        self._pwm = PWM(Pin(pin_num))
        self._pwm.duty_u16(0)
    def set_freq(self, hz: float):
        self._pwm.freq(int(hz))
    def set_duty(self, duty_0_1: float):
        d = max(0.0, min(1.0, float(duty_0_1)))
        self._pwm.duty_u16(int(d * 65535))
    def stop(self):
        self._pwm.duty_u16(0)

class FakePWMDriver(_BasePWM):
    def __init__(self, pin_num: int = PIN_BUZZER):
        self.freq = None; self.duty = 0.0; self.stopped = False
    def set_freq(self, hz: float): self.freq = float(hz)
    def set_duty(self, duty_0_1: float): self.duty = max(0.0, min(1.0, float(duty_0_1)))
    def stop(self): self.duty = 0.0; self.stopped = True

def make_pwm_driver(pin_num: int = PIN_BUZZER):
    if SIMULATION or not _MICROPY:
        return FakePWMDriver(pin_num)
    return RealPWMDriver(pin_num)
