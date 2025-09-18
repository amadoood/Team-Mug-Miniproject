# tests/test_controller_initial.py
# Tests your original ui/controller.py with your own mocks and storage.
# No dependency on the teammate's sequencer.

import os, sys, time

# --- Make project root importable when running from /tests ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.controller import Controller, DEBOUNCE_MS
from storage.pattern_io import PatternStore
from mocks.mock_hal_ui import MockUI
from mocks.mock_sequencer import MockSequencer

TEST_DIR = "./patterns_controller_initial"

def _clean_dir(path):
    try:
        for f in os.listdir(path):
            try:
                os.remove(path + "/" + f)
            except:
                pass
        os.rmdir(path)
    except Exception:
        pass

def assert_in_log(ui, entry, msg):
    if entry not in ui.log:
        raise AssertionError(f"{msg}\nExpected entry {entry} in ui.log, got:\n{ui.log}")

def run_tests():
    print("== Controller (initial) focused tests ==")
    _clean_dir(TEST_DIR)

    ui = MockUI()
    store = PatternStore(TEST_DIR)
    seq = MockSequencer()
    ctl = Controller(seq, store, ui)

    # --- 1) PLAY with no content -> ERR blink
    ctl.enqueue_button("PLAY")
    ctl.poll()
    assert_in_log(ui, ("LED", "ERR", True), "PLAY without content should blink ERR")

    # --- 2) REC toggle on/off updates LED (respect debounce)
    ctl.enqueue_button("REC"); ctl.poll()   # start recording
    assert ui.led["REC"] is True, "REC LED should be ON after first REC press"

    time.sleep((DEBOUNCE_MS + 10) / 1000.0)  # ensure next REC isn't debounced
    ctl.enqueue_button("REC"); ctl.poll()    # stop recording
    assert ui.led["REC"] is False, "REC LED should be OFF after second REC press"

    # --- 3) SAVE with no events -> ERR blink
    ctl.enqueue_button("SAVE"); ctl.poll()
    assert_in_log(ui, ("LED", "ERR", True), "SAVE with no events should blink ERR")

    # --- 4) Inject events, WAIT past debounce, SAVE -> file created, LED feedback
    seq.inject_dummy_events(n=3)

    # 👇 This wait is the critical fix: avoid SAVE debouncing
    time.sleep((DEBOUNCE_MS + 10) / 1000.0)

    ctl.enqueue_button("SAVE"); ctl.poll()
    assert_in_log(ui, ("LED", "SAVE", True), "SAVE should flash SAVE LED")
    names = store.list_patterns()
    assert len(names) >= 1, "Expected at least one saved pattern"

    # --- 5) LOAD -> events imported into sequencer, LED feedback
    ctl.enqueue_button("LOAD"); ctl.poll()
    assert_in_log(ui, ("LED", "LOAD", True), "LOAD should flash LOAD LED")

    # --- 6) PLAY -> LED on, STOP -> LEDs off
    ctl.enqueue_button("PLAY"); ctl.poll()
    assert ui.led["PLAY"] is True, "PLAY LED should be ON after PLAY"

    ctl.enqueue_button("STOP"); ctl.poll()
    assert ui.led["PLAY"] is False and ui.led["REC"] is False, "LEDs OFF after STOP"

    # --- 7) Debounce check: rapid duplicate press is ignored
    ctl.enqueue_button("REC"); ctl.poll()  # turn REC on
    ctl._last_press_ms["REC"] = ctl._last_press_ms["REC"] + DEBOUNCE_MS - 5
    ctl.enqueue_button("REC"); ctl.poll()
    assert ui.led["REC"] is True, "Second REC within debounce should be ignored (LED stays ON)"

    print("PASS: Controller initial file behaves as expected.")
    _clean_dir(TEST_DIR)

if __name__ == "__main__":
    run_tests()
