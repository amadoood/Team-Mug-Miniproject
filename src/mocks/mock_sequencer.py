# mocks/mock_sequencer.py
from models.types import NoteEvent

class MockSequencer:
    def __init__(self):
        self._events: list[NoteEvent] = []
        self._recording = False
        self._playing = False
        self._bpm = 120
        self._channels = 1

    # API used by Controller
    def start_recording(self): self._recording = True
    def stop_recording(self): self._recording = False
    def start_playback(self, loop=True): self._playing = True
    def stop_playback(self): self._playing = False
    def panic_all_notes_off(self): pass
    def has_content(self) -> bool: return len(self._events) > 0
    def get_bpm(self) -> int: return self._bpm
    def get_channels(self) -> int: return self._channels

    # Storage bridge
    def export_events_rows(self) -> list:
        return [e.to_row() for e in self._events]

    def import_events_rows(self, rows: list):
        self._events = [NoteEvent.from_row(r) for r in rows]

    # Helpers for tests/demo
    def inject_dummy_events(self, n=5, base_t=0):
        self._events = []
        for i in range(n):
            self._events.append(NoteEvent(channel=0, timestamp_ms=base_t + i*250,
                                          magnitude=0.8, pitch=60+i))
