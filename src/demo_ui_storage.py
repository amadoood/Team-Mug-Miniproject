# demo_ui_storage.py
from models.types import NoteEvent
from storage.pattern_io import PatternStore
from ui.controller import Controller
from mocks.mock_hal_ui import MockUI
from mocks.mock_sequencer import MockSequencer

def main():
    ui = MockUI()
    store = PatternStore("./patterns_demo")
    seq = MockSequencer()
    ctl = Controller(seq, store, ui)

    # Pretend we recorded 5 events
    seq.inject_dummy_events(n=5)

    # Save them
    ctl.enqueue_button("SAVE")
    ctl.poll()

    # Load and play
    ctl.enqueue_button("LOAD")
    ctl.poll()
    ctl.enqueue_button("PLAY")
    ctl.poll()

    print("LED states:", ui.led)
    print("Patterns:", store.list_patterns())

if __name__ == "__main__":
    main()
