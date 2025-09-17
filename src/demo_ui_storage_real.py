from ui.controller import Controller
from storage.pattern_io import PatternStore
from mocks.mock_hal_ui import MockUI
from core.sequencer import Sequencer
from models.types import NoteEvent
import time

def main():
    ui = MockUI()
    store = PatternStore("./patterns_demo")
    seq = Sequencer(bpm=120)

    ctl = Controller(seq, store, ui)

    # Simulate "record" by injecting a few events through the sequencer
    seq.start_recording()
    seq.record_event(NoteEvent(0, 0, 0.8, 60))
    time.sleep(0.25)
    seq.record_event(NoteEvent(0, 0, 0.8, 62))
    time.sleep(0.25)
    seq.record_event(NoteEvent(0, 0, 0.8, 64))
    seq.stop_recording()

    # SAVE via UI
    ctl.enqueue_button("SAVE"); ctl.poll()

    # LOAD via UI (into sequencer), then PLAY
    ctl.enqueue_button("LOAD"); ctl.poll()
    ctl.enqueue_button("PLAY"); ctl.poll()

    print("LED states:", ui.led)
    print("Patterns:", store.list_patterns())
    print("Seq summary:", seq.summary())

if __name__ == "__main__":
    main()
