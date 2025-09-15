"""
goal: give the rest of the code a simple way to ask "how bright is it right now?"
between 0-10.
how it works: reads the pico 16-bit adc, (0-65535), average a few samaples to reduce
noise, then normalizes to 0.0-1.0

why:
pin/tuning from pins.py: no hard-coding, so if wiring or smoothing changes, can edit
one file.
averaging: quick, low cpu-smoothing that helps with flicker and sensor noise

two methods:
read_raw --> integer (0 - 65535)
read_norm --> float (0.0 - 1.0)

"""