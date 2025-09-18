# Smoke test with a fake 'machine' module to run HAL on a laptop.

import os, sys, types
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# ---- Fake MicroPython 'machine' API ----
class _ADC:
    def __init__(self, pin):
        self.pin = pin
        self._vals = [1000, 2000, 3000, 4000]  # deterministic sequence
        self._i = 0
    def read_u16(self):
        v = self._vals[self._i % len(self._vals)]
        self._i += 1
        return v

class _Pin:
    def __init__(self, pin_num): self.pin_num = pin_num

class _PWM:
    def __init__(self, pin):
        self.pin = pin
        self.calls = []  # track call order
    def freq(self, hz: int):
        self.calls.append(("freq", int(hz)))
    def duty_u16(self, duty: int):
        self.calls.append(("duty", int(duty)))

# Inject fake 'machine' BEFORE importing HAL modules
fake_machine = types.SimpleNamespace(ADC=_ADC, Pin=_Pin, PWM=_PWM)
sys.modules['machine'] = fake_machine

# ---- Import HAL after faking 'machine' ----
import config.pins as p
from hal import adc_reader, pwm_audio

# Avoid sleeping in tests
pwm_audio.time.sleep_ms = lambda ms: None  # monkeypatch

# ---- Test ADCReader behavior ----
adc = adc_reader.ADCReader(samples=4)
raw = adc.read_raw()  # avg of [1000,2000,3000,4000] = 2500
norm = adc.read_norm()
assert raw == 2500, f"expected 2500, got {raw}"
assert 0.0 < norm < 1.0 and abs(norm - (2500/65535)) < 1e-6
print("OK - ADCReader avg & norm:", raw, round(norm, 6))

# ---- Test PWMAudio call order & clamping ----
bz = pwm_audio.PWMAudio()

# record starting length (constructor already did a 'duty->0' to mute)
start = len(bz._pwm.calls)

bz.play_tone(440, 5, 0.5)  # short duration; sleep is patched

# We expect, within this call: duty->0, freq->≈440, duty->~32767, ... final duty->0
slice_calls = bz._pwm.calls[start:start+3]
names = [name for name, _ in slice_calls]
assert names == ["duty", "freq", "duty"], f"bad order inside play_tone: {names}"

# frequency should have been set to ~440 Hz
freq_vals = [val for name, val in slice_calls if name == "freq"]
assert freq_vals and abs(freq_vals[0] - 440) <= 1, f"freq not ~440: {freq_vals}"

# final call overall should end with duty->0 (clean stop)
last_name, last_val = bz._pwm.calls[-1]
assert last_name == "duty" and last_val == 0, f"final not duty->0: {bz._pwm.calls[-1]}"

print("OK - PWMAudio call order and freq:", slice_calls)
print("OK - all fake-hardware smoke tests passed")
