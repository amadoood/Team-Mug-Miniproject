# Minimal laptop sanity checks (no hardware required).

import os, sys
# Let this script import from ./src
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

def ok(msg): print("OK -", msg)

# 1) config imports and values look sane
import config.pins as p
assert isinstance(p.PIN_LDR_ADC, int)
assert 0.0 <= p.TONE_DUTY <= 1.0
ok(f"config imported (PIN_LDR_ADC={p.PIN_LDR_ADC}, TONE_DUTY={p.TONE_DUTY})")

# 2) HAL modules import cleanly
from hal.adc_reader import ADCReader
from hal.pwm_audio import PWMAudio
ok("hal modules imported")

# 3) Constructing drivers off-device should raise (expected)
try:
    ADCReader()
    raise SystemExit("FAIL - ADCReader constructed on laptop (should raise)")
except RuntimeError:
    ok("ADCReader refuses to construct on laptop (expected)")

try:
    PWMAudio()
    raise SystemExit("FAIL - PWMAudio constructed on laptop (should raise)")
except RuntimeError:
    ok("PWMAudio refuses to construct on laptop (expected)")

ok("all laptop checks passed")
