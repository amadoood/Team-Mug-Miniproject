"""
run_all_tests_unified.py — run *all* laptop tests (storage/UI + HAL/Synth/Orchestrator + Storage↔Audio integration)

Usage:
  cd <repo>/src
  python -m run_all_tests_unified
"""
import os, sys, time as _t

THIS = os.path.dirname(__file__)
if THIS not in sys.path:
    sys.path.insert(0, THIS)

# Make sure desktop has MicroPython-style time helpers
if not hasattr(_t, "ticks_ms"): _t.ticks_ms = lambda: int(_t.time()*1000)
if not hasattr(_t, "ticks_diff"): _t.ticks_diff = lambda a,b: a-b
if not hasattr(_t, "sleep_ms"): _t.sleep_ms = lambda ms: _t.sleep(ms/1000.0)

def run_storage_suite() -> int:
    """Runs your original storage/UI test runner (no hardware)."""
    try:
        import run_all_tests as storage_runner
        print("\n=== Storage/UI suite ===")
        rc = 0
        try:
            storage_runner.main()  # your runner prints PASS and returns None
        except SystemExit as se:
            rc = int(se.code or 0)
        return rc
    except Exception as e:
        print("[FAIL] storage/UI suite:", e)
        return 1

def run_orchestra_suite() -> int:
    """Runs the laptop coherence suite for HAL/Synth/Mapper/Orchestrator."""
    try:
        import run_all_tests_all as orch_runner
        print("\n=== Orchestrator/HAL/Synth suite ===")
        try:
            orch_runner.main()  # raises SystemExit(code)
        except SystemExit as se:
            return int(se.code or 0)
    except Exception as e:
        print("[FAIL] orchestrator/HAL/Synth suite:", e)
        return 1
    return 0

def test_storage_plus_audio_path():
    """Save synth settings + a sequence via storage, reload, then play it through HAL/Synth."""
    import os, time as _t
    from integration.audio_storage_bridge import (
        DefaultStorage, save_synth_settings, load_synth_settings,
        save_sequence, load_sequence
    )
    from hal.pwm_audio import PWMAudio
    from audio.synth import Synth

    # temp data dir next to this script
    base = os.path.join(THIS, "_tmpdata_unified")
    st = DefaultStorage(base)

    # 1) Create synth, tweak settings, persist
    a = PWMAudio()
    s = Synth(a, vol_default=0.5) if "vol_default" in Synth.__init__.__code__.co_varnames else Synth(a)
    s.set_envelope(attack_ms=10, decay_ms=40, sustain_level=0.6, release_ms=60)
    s.set_volume(0.5)
    save_synth_settings(st, "synth_settings_demo", s)

    # 2) Make a short sequence and persist
    seq = [
        {"pitch": 60, "velocity": 0.6, "duration_ms": 120},  # C4
        {"pitch": 64, "velocity": 0.6, "duration_ms": 120},  # E4
        {"pitch": 67, "velocity": 0.6, "duration_ms": 160},  # G4
    ]
    save_sequence(st, "seq_demo", seq)

    # 3) Load settings into a fresh synth and play the loaded sequence
    a2 = PWMAudio()
    s2 = Synth(a2, vol_default=0.1) if "vol_default" in Synth.__init__.__code__.co_varnames else Synth(a2)
    load_synth_settings(st, "synth_settings_demo", s2)
    loaded = load_sequence(st, "seq_demo")

    now = _t.ticks_ms()
    for ev in loaded:
        s2.note_on(ev["pitch"], velocity=ev["velocity"], duration_ms=ev["duration_ms"], now_ms=now)
        # tick for note duration + a small release tail
        end = now + ev["duration_ms"] + 80
        while _t.ticks_diff(end, now) > 0:
            s2.tick(now)
            now += 10

    kinds = [k for (k, _) in a2._pwm.calls]
    if "freq" not in kinds or "duty" not in kinds:
        raise AssertionError("Combined path did not drive HAL (freq/duty missing)")
    print("[PASS] Storage<->Audio: settings+sequence persisted and played")

def run_storage_audio_integration_suite() -> int:
    """Wrapper to run the integration test and return 0/1."""
    print("\n=== Storage↔Audio integration suite ===")
    try:
        test_storage_plus_audio_path()
        return 0
    except SystemExit as se:
        return int(se.code or 0)
    except Exception as e:
        print("[FAIL] storage↔audio integration:", e)
        return 1

def main():
    print(f"Python: {sys.version.split()[0]}")
    print(f"CWD: {os.getcwd()}")
    print("Suites: storage/UI + orchestrator/HAL/Synth + storage↔audio integration\n")

    rc1 = run_storage_suite()
    rc2 = run_orchestra_suite()
    rc3 = run_storage_audio_integration_suite()

    total_rc = 0 if (rc1 == 0 and rc2 == 0 and rc3 == 0) else 1
    print("\n=== Summary ===")
    print(f"Storage/UI suite:           {'PASS' if rc1 == 0 else 'FAIL'}")
    print(f"Orchestrator/HAL/Synth:     {'PASS' if rc2 == 0 else 'FAIL'}")
    print(f"Storage↔Audio integration:   {'PASS' if rc3 == 0 else 'FAIL'}")
    print(f"\nOverall: {'ALL PASS ✅' if total_rc == 0 else 'SOMETHING FAILED ❌'}")
    raise SystemExit(total_rc)

if __name__ == "__main__":
    main()
