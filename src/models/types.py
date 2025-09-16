# models/types.py
try:
    import ujson as json  # noqa: F401
except Exception:  # CPython
    import json  # noqa: F401

class NoteEvent:
    __slots__ = ("channel", "timestamp_ms", "magnitude", "pitch", "duration_ms")

    def __init__(self, channel: int, timestamp_ms: int, magnitude: float,
                 pitch: int | None = None, duration_ms: int | None = None):
        self.channel = int(channel)
        self.timestamp_ms = int(timestamp_ms)
        self.magnitude = float(magnitude)
        self.pitch = int(pitch) if pitch is not None else None
        self.duration_ms = int(duration_ms) if duration_ms is not None else None

    def to_row(self):
        # Compact list form for storage: [t, ch, mag, pitch?, dur?]
        return [
            self.timestamp_ms,
            self.channel,
            round(self.magnitude, 4),
            self.pitch,
            self.duration_ms,
        ]

    @staticmethod
    def from_row(row):
        t, ch, mag, pitch, dur = row
        return NoteEvent(ch, t, mag, pitch, dur)
