# tests/test_hal_guard.py
import os, sys, unittest
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

class TestHalGuards(unittest.TestCase):
    def test_adcreader_refuses_on_laptop(self):
        from hal.adc_reader import ADCReader
        with self.assertRaises(RuntimeError):
            ADCReader()

    def test_pwmaudio_refuses_on_laptop(self):
        from hal.pwm_audio import PWMAudio
        with self.assertRaises(RuntimeError):
            PWMAudio()

if __name__ == "__main__":
    unittest.main()
