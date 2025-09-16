# models/types.py

class NoteEvent:
    """
    Minimal musical event used across the app.
    pitch: MIDI-style int (0..127) or None (if mapping happens later)
    magnitude: 0.0..1.0 (acts like velocity)
    channel: e.g., sensor index
    timestamp_ms: track-relative (ms) when recording; used for playback scheduling
    duration_ms: optional, may be None
    """
    __slots__ = ("channel", "timestamp_ms", "magnitude", "pitch", "duration_ms")

    def __init__(self, channel, timestamp_ms, magnitude, pitch=None, duration_ms=None):
        self.channel = int(channel)
        self.timestamp_ms = int(timestamp_ms)
        self.magnitude = float(magnitude)
        self.pitch = int(pitch) if pitch is not None else None
        self.duration_ms = int(duration_ms) if duration_ms is not None else None

    def __repr__(self):
        return ("NoteEvent(ch=%s, t=%sms, mag=%.2f, pitch=%s, dur=%s)" %
                (self.channel, self.timestamp_ms, self.magnitude, self.pitch, self.duration_ms))
