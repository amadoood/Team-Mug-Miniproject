# ui/controller.py
# Controller that will later talk to hardware; for Sprint 1 we mock buttons/LEDs.

try:
    import uasyncio as asyncio  # noqa: F401
except Exception:
    # Fallback no-async needed for tests
    asyncio = None

try:
    from time import ticks_ms
except Exception:
    import time
    ticks_ms = lambda: int(time.time() * 1000)  # noqa: E731

DEBOUNCE_MS = 120

class Controller:
    """
    Controller mediates between UI inputs and Sequencer/Storage.
    In Sprint 1, UI is mocked by injecting events via enqueue_button().
    LEDs are logged via ui_backend.set_led(name, on).
    """

    def __init__(self, sequencer, store, ui_backend):
        self.seq = sequencer
        self.store = store
        self.ui = ui_backend
        self.state = "IDLE"  # IDLE | RECORDING | PLAYING | ERROR
        self._last_press_ms = {}
        self._queue = []  # list of (btn_name, t_ms)
        self._current_pattern_name = "take1"

    # --- Mock input injection (for tests/demo) ---
    def enqueue_button(self, name: str):
        self._queue.append((name, ticks_ms()))

    # --- Poll loop (call periodically) ---
    def poll(self):
        # drain one event at a time to keep deterministic behavior
        if not self._queue:
            return
        name, t = self._queue.pop(0)

        # debouncing
        last = self._last_press_ms.get(name, 0)
        if t - last < DEBOUNCE_MS:
            return
        self._last_press_ms[name] = t

        # handle event
        try:
            if name == "REC":
                if self.state != "RECORDING":
                    self.seq.start_recording()
                    self.ui.set_led("REC", True)
                    self.ui.set_led("PLAY", False)
                    self.state = "RECORDING"
                else:
                    self.seq.stop_recording()
                    self.ui.set_led("REC", False)
                    self.state = "IDLE"

            elif name == "PLAY":
                if self.state != "PLAYING":
                    # Only allow play if there's something to play
                    if self.seq.has_content():
                        self.seq.start_playback(loop=True)
                        self.ui.set_led("PLAY", True)
                        self.ui.set_led("REC", False)
                        self.state = "PLAYING"
                    else:
                        self._error_blink()
                else:
                    self.seq.stop_playback()
                    self.ui.set_led("PLAY", False)
                    self.state = "IDLE"

            elif name == "STOP":
                self.seq.stop_playback()
                self.seq.stop_recording()
                self.seq.panic_all_notes_off()
                self.ui.set_led("PLAY", False)
                self.ui.set_led("REC", False)
                self.state = "IDLE"

            elif name == "SAVE":
                # Ask sequencer for events snapshot
                events_rows = self.seq.export_events_rows()
                if not events_rows:
                    self._error_blink()
                else:
                    meta = {"bpm": self.seq.get_bpm(), "channels": self.seq.get_channels()}
                    self.store.save(self._current_pattern_name, meta, events_rows)
                    self.ui.flash("SAVE", times=2)

            elif name == "LOAD":
                names = self.store.list_patterns()
                if not names:
                    self._error_blink()
                else:
                    # For Sprint 1: just load the first name (round-robin later)
                    meta, rows = self.store.load(names[0])
                    self.seq.import_events_rows(rows)
                    self._current_pattern_name = names[0]
                    self.ui.flash("LOAD", times=2)

            else:
                # Unknown button: ignore
                pass

        except Exception:
            self._error_blink()

    def _error_blink(self):
        self.state = "ERROR"
        self.ui.flash("ERR", times=3)
        self.state = "IDLE"
