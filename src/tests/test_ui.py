# tests/test_ui.py
from ui.controller import Controller
from storage.pattern_io import PatternStore
from mocks.mock_hal_ui import MockUI
from mocks.mock_sequencer import MockSequencer
import os

TEST_DIR = "./patterns_test_ui"

def _clean():
    try:
        for f in os.listdir(TEST_DIR):
            os.remove(TEST_DIR + "/" + f)
        os.rmdir(TEST_DIR)
    except Exception:
        pass

def run_tests():
    print("== UI tests ==")
    _clean()
    ui = MockUI()
    store = PatternStore(TEST_DIR)
    seq = MockSequencer()
    ctl = Controller(seq, store, ui)

    # PLAY with no content -> error blink
    ctl.enqueue_button("PLAY")
    ctl.poll()
    assert ("LED", "ERR", True) in ui.log, "Expected error blink when no content"

    # Record toggle (start/stop)
    ctl.enqueue_button("REC")
    ctl.poll()
    assert ui.led["REC"] is True
    ctl.enqueue_button("REC")
    ctl.poll()
    assert ui.led["REC"] is False

    # Inject events, SAVE, then LOAD, PLAY
    seq.inject_dummy_events(n=3)
    ctl.enqueue_button("SAVE")
    ctl.poll()
    assert ("LED", "SAVE", True) in ui.log

    ctl.enqueue_button("LOAD")
    ctl.poll()
    assert ("LED", "LOAD", True) in ui.log

    ctl.enqueue_button("PLAY")
    ctl.poll()
    assert ui.led["PLAY"] is True

    # STOP should clear LEDs and states
    ctl.enqueue_button("STOP")
    ctl.poll()
    assert ui.led["PLAY"] is False and ui.led["REC"] is False

    print("All UI tests passed.")
    _clean()

if __name__ == "__main__":
    run_tests()
