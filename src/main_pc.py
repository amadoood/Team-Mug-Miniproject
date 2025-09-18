# main_pc.py — desktop runner that patches time helpers and runs the orchestrator

import time as _t

# Add MicroPython-style time helpers if missing
if not hasattr(_t, "ticks_ms"):
    _t.ticks_ms = lambda: int(_t.time() * 1000)
if not hasattr(_t, "ticks_diff"):
    _t.ticks_diff = lambda a, b: a - b
if not hasattr(_t, "sleep_ms"):
    _t.sleep_ms = lambda ms: _t.sleep(ms / 1000.0)

from audio.orchestrator import LightOrchestra

def main():
    print("Starting Light Orchestra (desktop mode)...")
    try:
        LightOrchestra().run()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt: stopping.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
