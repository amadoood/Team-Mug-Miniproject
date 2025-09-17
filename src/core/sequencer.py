# core/sequencer.py
# MicroPython-friendly
try:
    from utime import ticks_ms, ticks_diff
except Exception:
    from time import monotonic_ns
    def ticks_ms(): return int(monotonic_ns() // 1_000_000)
    def ticks_diff(a, b): return a - b

from models.types import NoteEvent

class Sequencer:
    """
    States: IDLE -> RECORDING -> PLAYING
    - Records NoteEvents with track-relative timestamps.
    - tick() returns due events during playback.
    - Matches Pat's Controller/Storage expectations.
    """

    IDLE, RECORDING, PLAYING = 0, 1, 2

    def __init__(self, bpm=120, quantize_ms=0, beats_per_bar=4, channels=1):
        self._state = self.IDLE
        self._events: list[NoteEvent] = []
        self._bpm = int(bpm)
        self._quantize_ms = max(0, int(quantize_ms))
        self._beats_per_bar = max(1, int(beats_per_bar))
        self._channels = int(channels)

        # rec
        self._rec_t0_ms: int | None = None

        # play
        self._loop = True
        self._play_t0_ms: int | None = None
        self._last_tick_ms: int | None = None
        self._play_idx = 0
        self._track_len_ms = 0

    # -------- Controller-required API --------
    def start_recording(self):  # used by Controller
        self.stop_playback()
        self._events.clear()
        self._rec_t0_ms = ticks_ms()
        self._state = self.RECORDING
        self._track_len_ms = 0

    def stop_recording(self):   # used by Controller
        if self._state != self.RECORDING:
            return
        self._state = self.IDLE
        last_t = self._events[-1].timestamp_ms if self._events else 0
        bar = self._beat_ms() * self._beats_per_bar
        self._track_len_ms = _round_up(last_t, bar) if self._loop else last_t

    def start_playback(self, loop=True):  # used by Controller
        self._loop = bool(loop)
        self._play_idx = 0
        self._play_t0_ms = ticks_ms()
        self._last_tick_ms = self._play_t0_ms
        if self._track_len_ms <= 0:
            self._track_len_ms = self._events[-1].timestamp_ms if self._events else 0
        self._state = self.PLAYING

    def stop_playback(self):  # used by Controller
        if self._state == self.PLAYING:
            self._state = self.IDLE
        self._play_t0_ms = None
        self._last_tick_ms = None
        self._play_idx = 0

    def panic_all_notes_off(self):  # used by Controller
        # No synth dependency here; ensure playback halted
        self.stop_playback()

    def has_content(self) -> bool:  # used by Controller
        return len(self._events) > 0

    def get_bpm(self) -> int:       # used by Controller/Storage
        return self._bpm

    def get_channels(self) -> int:  # used by Controller/Storage
        return self._channels

    def export_events_rows(self) -> list:  # used by Storage
        return [e.to_row() for e in self._events]

    def import_events_rows(self, rows: list):  # used by Storage
        self._events = [NoteEvent.from_row(r) for r in rows]
        # recompute track length
        self._track_len_ms = self._events[-1].timestamp_ms if self._events else 0
        self._state = self.IDLE
        self._play_idx = 0

    # -------- Recording hook from Signal layer --------
    def record_event(self, event: NoteEvent) -> None:
        if self._state != self.RECORDING or self._rec_t0_ms is None:
            return
        rel = ticks_diff(ticks_ms(), self._rec_t0_ms)
        e = NoteEvent(event.channel, int(rel), event.magnitude, event.pitch, event.duration_ms)
        if self._quantize_ms > 0:
            e.timestamp_ms = _quantize(e.timestamp_ms, self._quantize_ms)
        if not self._events or e.timestamp_ms >= self._events[-1].timestamp_ms:
            self._events.append(e)
        else:
            i = _bisect_right_by_time(self._events, e.timestamp_ms)
            self._events.insert(i, e)

    # -------- Playback scheduling (call ~every 5–15ms) --------
    def tick(self, now_ms: int | None = None) -> list[NoteEvent]:
        if self._state != self.PLAYING or self._play_t0_ms is None:
            return []
        now = ticks_ms() if now_ms is None else int(now_ms)

        prev_tick = self._last_tick_ms if self._last_tick_ms is not None else now
        self._last_tick_ms = now

        if not self._events:
            if self._loop and self._track_len_ms > 0:
                elapsed = ticks_diff(now, self._play_t0_ms)
                if elapsed >= self._track_len_ms:
                    loops = elapsed // self._track_len_ms
                    self._play_t0_ms += loops * self._track_len_ms
            return []

        out: list[NoteEvent] = []
        elapsed = ticks_diff(now, self._play_t0_ms)

        if self._loop and self._track_len_ms > 0:
            t_in = elapsed % self._track_len_ms
            prev_in = ticks_diff(prev_tick, self._play_t0_ms) % self._track_len_ms
            if t_in >= prev_in:
                s = _bisect_right_by_time(self._events, prev_in)
                e = _bisect_right_by_time(self._events, t_in)
                out.extend(self._events[s:e])
            else:
                s = _bisect_right_by_time(self._events, prev_in)
                out.extend(self._events[s:])
                e = _bisect_right_by_time(self._events, t_in)
                out.extend(self._events[:e])
            self._play_idx = _bisect_right_by_time(self._events, t_in)
            return out

        # non-looping
        n = len(self._events)
        while self._play_idx < n and self._events[self._play_idx].timestamp_ms <= elapsed:
            out.append(self._events[self._play_idx])
            self._play_idx += 1
        if self._play_idx >= n and not self._loop:
            self.stop_playback()
        return out

    # -------- Utility / config --------
    def summary(self) -> dict:
        return {
            "state": self._state, "bpm": self._bpm, "quantize_ms": self._quantize_ms,
            "beats_per_bar": self._beats_per_bar, "events": len(self._events),
            "track_len_ms": self._track_len_ms, "loop": self._loop,
        }

    def _beat_ms(self) -> int:
        return int(60000 // max(1, self._bpm))


# ---- helpers ----
def _quantize(t_ms, q_ms):
    if q_ms <= 0: return int(t_ms)
    return int((t_ms + q_ms // 2) // q_ms) * q_ms

def _round_up(val, base):
    if base <= 0: return int(val)
    return int(((val + base - 1) // base) * base)

def _bisect_right_by_time(events, t_ms):
    lo, hi = 0, len(events)
    while lo < hi:
        mid = (lo + hi) // 2
        if events[mid].timestamp_ms <= t_ms:
            lo = mid + 1
        else:
            hi = mid
    return lo
