"""
ADCReader — minimal light sensor driver (Pico 2WH, GP28/ADC2 by default).

Public API (MVP):
    read_raw()  -> int    # averaged 16-bit ADC value (0..65535)
    read_norm() -> float  # normalized light level (0.0..1.0)

Notes:
- Uses pin/tunables from config.pins (single source of truth).
- Importing this file on a laptop is fine; instantiating the class requires MicroPython.
"""

from config.pins import PIN_LDR_ADC, ADC_SAMPLES


# Try MicroPython hardware; if unavailable (laptop), keep import safe
#import and environment guard
"""
pulls the pin and sample count from the central config (pins.py)
tries to import machine.ADC (only on pico)
if available (=True) hardware mode
if not (=False)import this on laptop as hardware unavailable
"""
try:
    from machine import ADC  # MicroPython hardware ADC
    _MICROPY = True
except Exception:
    ADC = None
    _MICROPY = False



class ADCReader:
    def __init__(self, adc_pin: int = PIN_LDR_ADC, samples: int = ADC_SAMPLES):
        """
        adc_pin: Pico GPIO that supports ADC (GP28 default).
        samples: number of raw reads to average per call (>=1).
        stores how many raw reads to average samples, clamped to >= 1
        prevents misuse on a laptop; importing is fine, but constructing the driver
        without hardware raises a clear error
        creates the micropython adc object on gp28
        """
        self.samples = max(1, int(samples))

        if not _MICROPY:
            raise RuntimeError(
                "ADCReader requires MicroPython on the Pico (machine.ADC)."
            )

        # On Pico: construct ADC on the given GPIO pin (0..65535 reads)
        self._adc = ADC(adc_pin)


    def read_raw(self) -> int:
        """Return an averaged 16-bit raw ADC value (0..65535).
        calls read_u16()several times and averages them.
        averaging smooths noise a bit with very little cpu cost
        """
        total = 0
        for _ in range(self.samples):
            total += self._adc.read_u16()
        return total // self.samples


    def read_norm(self) -> float:
        """Return normalized light level in [0.0, 1.0].
        converts the 16bit value to a 0.0-1.0 float so other modules can use it directly
        """
        return self.read_raw() / 65535.0
