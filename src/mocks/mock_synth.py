# mocks/mock_synth.py
class MockSynth:
    def __init__(self):
        self.played = []

    def play_event(self, evt):
        self.played.append((evt.pitch, evt.magnitude, evt.duration_ms))
