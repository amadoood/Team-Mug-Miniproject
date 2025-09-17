# src/audio/synth.py

class Synth:
    """
    Minimal PWM synth: mono voice, ADSR-lite, non-blocking.
    Orchestrator must call tick(now_ms) every ~10 ms.
    """

    def __init__(self, pwm_driver, *, max_voices=1, vol_default=0.6):
        self.pwm = pwm_driver
        self.master = float(vol_default)
        self.env = {"attack_ms": 5, "decay_ms": 30, "sustain": 0.7, "release_ms": 40}
        self.voice = None  # mono for v1
        self.active = False

    @staticmethod
    def midi_to_hz(pitch: int) -> float:
        if not (0 <= pitch <= 127):
            raise ValueError("pitch out of range 0..127")
        return 440.0 * (2 ** ((pitch - 69) / 12.0))

    def set_envelope(self, *, attack_ms=5, decay_ms=30, sustain_level=0.7, release_ms=40):
        if not (0.0 <= sustain_level <= 1.0):
            raise ValueError("sustain_level must be 0..1")
        self.env = {"attack_ms": int(attack_ms), "decay_ms": int(decay_ms),
                    "sustain": float(sustain_level), "release_ms": int(release_ms)}

    def set_volume(self, master_vol_0_1: float):
        if not (0.0 <= master_vol_0_1 <= 1.0):
            raise ValueError("volume must be 0..1")
        self.master = float(master_vol_0_1)

    def note_on(self, pitch: int, velocity: float = 1.0, *, duration_ms=None, now_ms: int = 0) -> int:
        if not (0.0 <= velocity <= 1.0):
            raise ValueError("velocity must be 0..1")
        freq = self.midi_to_hz(pitch)
        self.voice = {
            "pitch": pitch, "freq": freq, "vel": float(velocity),
            "t0": int(now_ms), "released": False, "t_release": None,
            "duration_ms": int(duration_ms) if duration_ms is not None else None,
            "level": 0.0
        }
        try:
            self.pwm.set_freq(freq)      # reduce start latency
            self.pwm.set_duty(0.0)
        except Exception:
            pass
        self.active = True
        return 0  # voice_id for mono

    def note_off(self, voice_id=None, *, pitch=None, now_ms: int = 0):
        if self.voice and not self.voice["released"]:
            self.voice["released"] = True
            self.voice["t_release"] = int(now_ms)

    def all_notes_off(self):
        self.voice = None
        self.active = False
        try:
            self.pwm.stop()
        except Exception:
            pass

    def play_event(self, event, now_ms: int = 0):
        dur = getattr(event, "duration_ms", None) if hasattr(event, "duration_ms") else None
        vel = getattr(event, "magnitude", getattr(event, "velocity", 1.0))
        return self.note_on(event.pitch, velocity=vel, duration_ms=dur, now_ms=now_ms)

    def tick(self, now_ms: int):
        """Advance envelope and update PWM duty. Call every ~10 ms."""
        v = self.voice
        if not v:
            return

        e = self.env
        t = max(0, int(now_ms) - v["t0"])

        # auto duration -> trigger release
        if v["duration_ms"] is not None and (not v["released"]) and t >= v["duration_ms"]:
            v["released"] = True
            v["t_release"] = int(now_ms)

        # envelope
        if not v["released"]:
            # Attack
            if e["attack_ms"] <= 0:
                level = 1.0
            else:
                level = min(1.0, t / float(e["attack_ms"]))
            # Decay toward sustain after attack
            if level >= 1.0:
                td = t - e["attack_ms"]
                if e["decay_ms"] <= 0:
                    level = e["sustain"]
                else:
                    td = max(0, td)
                    start, end = 1.0, e["sustain"]
                    # linear decay
                    level = end + (start - end) * max(0.0, 1.0 - td / float(e["decay_ms"]))
                    if td >= e["decay_ms"]:
                        level = end
            v["level"] = level
        else:
            # Release
            if e["release_ms"] <= 0:
                self.all_notes_off()
                return
            tr = max(0, int(now_ms) - int(v["t_release"]))
            start = v.get("level", e["sustain"])
            level = max(0.0, start * (1.0 - tr / float(e["release_ms"])))
            v["level"] = level
            if tr >= e["release_ms"] or level <= 0.0:
                self.all_notes_off()
                return

        # apply duty (clamped)
        duty = max(0.0, min(1.0, v["level"] * v["vel"] * self.master))
        try:
            self.pwm.set_duty(duty)
        except Exception:
            self.all_notes_off()

    # Debug helper for tests
    def debug_active_voices(self):
        return [] if not self.voice else [{
            "voice_id": 0, "pitch": self.voice["pitch"], "freq": self.voice["freq"],
            "level": self.voice["level"], "released": self.voice["released"]
        }]