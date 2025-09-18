# tests/test_hal_with_fakes.py
import os, sys, types, importlib, unittest
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# --- Fake MicroPython 'machine' API ---
class _ADC:
    def __init__(self, pin):
        self.pin = pin
        self._vals = [1000, 2000, 3000, 4000]
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
        self.calls = []  # list of ("freq"/"duty", value)
    def freq(self, hz: int): self.calls.append(("freq", int(hz)))
    def duty_u16(self, duty: int): self.calls.append(("duty", int(duty)))

class HalWithFakesTest(unittest.TestCase):
    def setUp(self):
        # Save any real 'machine' and inject fake
        self._old_machine = sys.modules.get("machine")
        sys.modules["machine"] = types.SimpleNamespace(ADC=_ADC, Pin=_Pin, PWM=_PWM)

        # Ensure fresh imports of HAL after injecting fake
        for mod in ("hal.adc_reader", "hal.pwm_audio"):
            if mod in sys.modules: del sys.modules[mod]
        self.adc_reader = importlib.import_module("hal.adc_reader")
        self.pwm_audio  = importlib.import_module("hal.pwm_audio")

        # Avoid real sleeps
        self.pwm_audio.time.sleep_ms = lambda ms: None

    def tearDown(self):
        # Restore previous 'machine'
        if self._old_machine is None:
            sys.modules.pop("machine", None)
        else:
            sys.modules["machine"] = self._old_machine

    def test_adcreader_avg_and_norm(self):
        adc = self.adc_reader.ADCReader(samples=4)
        raw = adc.read_raw()   # avg of 1000,2000,3000,4000 = 2500
        self.assertEqual(raw, 2500)
        self.assertAlmostEqual(adc.read_norm(), 2500/65535.0, places=6)

    def test_pwmaudio_order_and_stop(self):
        bz = self.pwm_audio.PWMAudio()
        start = len(bz._pwm.calls)  # constructor adds a duty->0
        bz.play_tone(440, 5, 0.5)
        calls = bz._pwm.calls[start:start+3]
        names = [n for n, _ in calls]
        self.assertEqual(names, ["duty", "freq", "duty"])  # pop-safe start
        # freq ~ 440
        freq_vals = [v for n, v in calls if n == "freq"]
        self.assertTrue(freq_vals and abs(freq_vals[0] - 440) <= 1)
        # final stop is duty->0
        self.assertEqual(bz._pwm.calls[-1], ("duty", 0))

    def test_pwmaudio_clamps_frequency(self):
        import config.pins as p
        bz = self.pwm_audio.PWMAudio()
        start = len(bz._pwm.calls)

        # too-low freq -> clamp to MIN_TONE_HZ
        bz.play_tone(p.MIN_TONE_HZ / 10.0, 1, 0.1)
        low_freq = [v for n, v in bz._pwm.calls[start:] if n == "freq"][0]
        self.assertEqual(low_freq, int(p.MIN_TONE_HZ))

        # clear and test high clamp
        bz._pwm.calls.clear()
        bz.play_tone(p.MAX_TONE_HZ * 10.0, 1, 0.1)
        high_freq = [v for n, v in bz._pwm.calls if n == "freq"][0]
        self.assertEqual(high_freq, int(p.MAX_TONE_HZ))

if __name__ == "__main__":
    unittest.main()
