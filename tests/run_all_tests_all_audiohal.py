"""
run_all_tests_all.py — laptop coherence tests (no hardware)
Run with:
  cd <repo>/src
  python -m run_all_tests_all
"""
import sys, os, time as _t

# ensure src is importable
THIS = os.path.dirname(__file__)
if THIS not in sys.path:
    sys.path.insert(0, THIS)

# add MicroPython-style time helpers if missing
if not hasattr(_t, "ticks_ms"): _t.ticks_ms = lambda: int(_t.time()*1000)
if not hasattr(_t, "ticks_diff"): _t.ticks_diff = lambda a,b: a-b
if not hasattr(_t, "sleep_ms"): _t.sleep_ms = lambda ms: _t.sleep(ms/1000.0)

PASSED = 0; FAILED = 0
ok   = lambda name: (globals().__setitem__("PASSED", PASSED+1), print(f"[PASS] {name}"))
fail = lambda name,e: (globals().__setitem__("FAILED", FAILED+1), print(f"[FAIL] {name}: {e}"))

def test_hal_pwm_audio():
    from hal.pwm_audio import PWMAudio
    from config.pins import MIN_TONE_HZ, MAX_TONE_HZ
    import hal.pwm_audio as mod
    if hasattr(mod, "time") and hasattr(mod.time, "sleep_ms"):
        try: mod.time.sleep_ms = lambda ms: None
        except Exception: pass
    a = PWMAudio()
    pwm = a._pwm
    a.play_tone(MAX_TONE_HZ+5000, duration_ms=10, volume=1.5)
    calls = pwm.calls[:]
    kinds = [k for (k,_) in calls]
    if not calls: raise AssertionError("No PWM calls recorded")
    if kinds[0] != "duty" or "freq" not in kinds or kinds[-1] != "duty":
        raise AssertionError(f"Unexpected call order: {kinds}")
    freqs = [v for k,v in calls if k == "freq"]
    if not freqs or not (MIN_TONE_HZ <= freqs[-1] <= MAX_TONE_HZ):
        raise AssertionError(f"Freq not clamped: {freqs[-1] if freqs else None}")
    for name in ("set_freq","set_duty","stop"):
        if not hasattr(a, name): raise AssertionError(f"PWMAudio missing {name}()")
    ok("HAL: pop-safe + clamp + non-blocking API")

def test_synth_envelope():
    from audio.synth import Synth
    from hal.pwm_audio import PWMAudio
    a = PWMAudio()
    s = Synth(a, vol_default=0.6) if "vol_default" in Synth.__init__.__code__.co_varnames else Synth(a)
    s.note_on(69, velocity=0.7, duration_ms=120, now_ms=0)
    for t in range(0, 200, 10): s.tick(t)
    kinds = [k for (k,_) in a._pwm.calls]
    if "freq" not in kinds or "duty" not in kinds:
        raise AssertionError(f"Synth didn’t drive HAL: {a._pwm.calls[:8]}")
    if hasattr(s, "all_notes_off"): s.all_notes_off()
    ok("Synth: note_on + tick drives HAL")

def test_mapper_event_and_bounds():
    from audio.light_to_note import LightToNoteMapper
    m = LightToNoteMapper()
    evt = m.create_note_event(50.0)
    for k in ("pitch","velocity","duration_ms"):
        if k not in evt: raise AssertionError(f"create_note_event missing {k}")
    if not (0 <= evt["velocity"] <= 1): raise AssertionError("velocity out of range")
    if not (0 <= evt["duration_ms"] <= 2000): raise AssertionError("duration looks odd")
    ok("Mapper: create_note_event coherent")

def test_orchestrator_ticks():
    from audio.orchestrator import LightOrchestra
    o = LightOrchestra()
    for _ in range(20):
        now = _t.ticks_ms()
        o.switches.update()
        o.update_light_reading(now)
        o.handle_switch_events()
        o.process_light_to_music(now)
        o.synth.tick(now)
        _t.sleep_ms(o.tick_interval_ms)
    ok("Orchestrator: steps without errors")

def main():
    print("=== Running laptop coherence suite ===")
    for fn in (test_hal_pwm_audio, test_synth_envelope, test_mapper_event_and_bounds, test_orchestrator_ticks):
        try: fn()
        except Exception as e: fail(fn.__name__, e)
    print(f"\nSummary: {PASSED} passed, {FAILED} failed")
    raise SystemExit(FAILED)

if __name__ == "__main__":
    main()
