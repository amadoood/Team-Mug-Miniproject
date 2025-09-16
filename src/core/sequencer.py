# core/sequencer.py
# MicroPython-friendly; avoids heavy typing features.
try:
    from utime import ticks_ms, ticks_diff
except ImportError:
    from time import monotonic_ns
    def ticks_ms():
        return int(monotonic_ns() // 1_000_000)
    def ticks_diff(a, b):
        return a - b

from models.types import NoteEvent

class Sequencer:
    """
    State machine: IDLE -> RECORDING -> PLAYING -> IDLE
    - Records NoteEvent objects with track-relative timestamps.
    - tick() returns events that become due since the last tick.
    - Supports BPM, optional quantization, and looping.
    """

    IDLE = 0
    RECORDING = 1
    PLAYING = 2

    def __init__(self, bpm=120, quantize_ms=0, beats_per_bar=4):
        self._state = self.IDLE
        self._events = []              # list of NoteEvent, timestamps are track-relative (ms)
        self._bpm = int(bpm)
        self._quantize_ms = max(0, int(quantize_ms))
        self._beats_per_bar = max(1, int(beats_per_bar))

        # Recording
        self._rec_t0_ms = None

        # Playback
        self._loop = True
        self._play_t0_ms = None
        self._last_tick_ms = None
        self._play_idx = 0
        self._track_len_ms = 0

    # ---------- Public API ----------

    def new_track(self, bpm=None, quantize_ms=None):
        self.stop_playback()
        self._events[:] = []
        self._track_len_ms = 0
        if bpm is not None:
            self.set_bpm(bpm)
        if quantize_ms is not None:
            self.set_quantize(quantize_ms)

    def start_recording(self):
        self.stop_playback()
        self._events[:] = []
        self._rec_t0_ms = ticks_ms()
        self._state = self.RECORDING
        self._track_len_ms = 0

    def stop_recording(self):
        if self._state != self.RECORDING:
            return
        self._state = self.IDLE
        last_t = self._events[-1].timestamp_ms if self._events else 0
        beat_ms = self._beat_ms()
        bar_ms = beat_ms * self._beats_per_bar
        self._track_len_ms = _round_up(last_t, bar_ms) if self._loop else last_t

    def record_event(self, event):
        if self._state != self.RECORDING or self._rec_t0_ms is None:
            return
        now = ticks_ms()
        rel = ticks_diff(now, self._rec_t0_ms)
        e = NoteEvent(
            channel=event.channel,
            timestamp_ms=int(rel),
            magnitude=event.magnitude,
            pitch=event.pitch,
            duration_ms=event.duration_ms
        )
        if self._quantize_ms > 0:
            e.timestamp_ms = _quantize(e.timestamp_ms, self._quantize_ms)

        if not self._events or e.timestamp_ms >= self._events[-1].timestamp_ms:
            self._events.append(e)
        else:
            i = _bisect_right_by_time(self._events, e.timestamp_ms)
            self._events.insert(i, e)

    def start_playback(self, loop=True):
        self._loop = bool(loop)
        self._play_idx = 0
        self._play_t0_ms = ticks_ms()
        self._last_tick_ms = self._play_t0_ms
        if self._track_len_ms <= 0:
            self._track_len_ms = self._events[-1].timestamp_ms if self._events else 0
        self._state = self.PLAYING

    def stop_playback(self):
        if self._state == self.PLAYING:
            self._state = self.IDLE
        self._play_t0_ms = None
        self._last_tick_ms = None
        self._play_idx = 0

    def tick(self, now_ms=None):
        if self._state != self.PLAYING or self._play_t0_ms is None:
            return []
        now = ticks_ms() if now_ms is None else int(now_ms)

        prev_last = self._last_tick_ms if self._last_tick_ms is not None else now
        self._last_tick_ms = now

        if not self._events:
            if self._loop and self._track_len_ms > 0:
                elapsed = ticks_diff(now, self._play_t0_ms)
                if elapsed >= self._track_len_ms:
                    loops = elapsed // self._track_len_ms
                    self._play_t0_ms += loops * self._track_len_ms
            return []

        out = []
        elapsed = ticks_diff(now, self._play_t0_ms)

        if self._loop and self._track_len_ms > 0:
            t_in = elapsed % self._track_len_ms
            prev_in = ticks_diff(prev_last, self._play_t0_ms) % self._track_len_ms

            if t_in >= prev_in:
                start_idx = _bisect_right_by_time(self._events, prev_in)
                end_idx = _bisect_right_by_time(self._events, t_in)
                out.extend(self._events[start_idx:end_idx])
            else:
                start_idx = _bisect_right_by_time(self._events, prev_in)
                out.extend(self._events[start_idx:])
                end_idx = _bisect_right_by_time(self._events, t_in)
                out.extend(self._events[:end_idx])

            self._play_idx = _bisect_right_by_time(self._events, t_in)
            return out

        n = len(self._events)
        while self._play_idx < n and self._events[self._play_idx].timestamp_ms <= elapsed:
            out.append(self._events[self._play_idx])
            self._play_idx += 1

        if self._play_idx >= n and (not self._loop):
            self.stop_playback()

        return out

    # ---------- Config / Info ----------

    def set_bpm(self, bpm):
        self._bpm = max(1, int(bpm))

    def get_bpm(self):
        return self._bpm

    def set_quantize(self, quantize_ms):
        self._quantize_ms = max(0, int(quantize_ms))

    def get_quantize(self):
        return self._quantize_ms

    def set_loop(self, loop):
        self._loop = bool(loop)

    def is_looping(self):
        return self._loop

    def get_state(self):
        return self._state

    def events(self):
        return list(self._events)

    def track_length_ms(self):
        return int(self._track_len_ms)

    def summary(self):
        return {
            "state": self._state,
            "bpm": self._bpm,
            "quantize_ms": self._quantize_ms,
            "beats_per_bar": self._beats_per_bar,
            "events": len(self._events),
            "track_len_ms": self._track_len_ms,
            "loop": self._loop,
        }

    # ---------- Internals ----------
    def _beat_ms(self):
        return int(60000 // max(1, self._bpm))


# ---------- Helpers ----------

def _quantize(t_ms, q_ms):
    if q_ms <= 0:
        return int(t_ms)
    return int((t_ms + q_ms // 2) // q_ms) * q_ms

def _round_up(val, base):
    if base <= 0:
        return int(val)
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
