# machine.py — desktop shim so CPython can import MicroPython-style code.
# NOTE: On the Pico you will NOT use this file; the real 'machine' module exists there.

import random

class Pin:
    IN = 0
    OUT = 1
    PULL_UP = 1

    def __init__(self, *args, **kwargs):
        pass

    # For pull-up switches, "1" means unpressed by default
    def value(self):
        return 1

    # no-op; present for API compatibility
    def irq(self, *args, **kwargs):
        pass


class ADC:
    def __init__(self, *args, **kwargs):
        pass

    # Mid-level value with a little noise, 0..65535
    def read_u16(self):
        base = 30000
        jitter = random.randint(-1200, 1200)
        return max(0, min(65535, base + jitter))


class PWM:
    def __init__(self, *args, **kwargs):
        self.calls = []  # helpful to assert in tests

    def freq(self, f):
        self.calls.append(("freq", int(f)))

    def duty_u16(self, d):
        self.calls.append(("duty", int(d)))

    def deinit(self):
        self.calls.append(("deinit", None))
