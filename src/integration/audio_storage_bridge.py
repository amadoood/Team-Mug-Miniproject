# integration/audio_storage_bridge.py
# Bridge between storage and audio (synth/HAL) for laptop + Pico.

import os, json

# ---------- Minimal portable storage (JSON-on-disk) ----------
class DefaultStorage:
    """Tiny JSON storage so tests can run on a laptop without your full storage stack."""
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, name: str) -> str:
        safe = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
        return os.path.join(self.base_dir, f"{safe}.json")

    def save_json(self, name: str, data: dict) -> None:
        with open(self._path(name), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_json(self, name: str) -> dict:
        p = self._path(name)
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)


# ---------- Synth settings I/O ----------
def save_synth_settings(storage, name: str, synth) -> None:
    """Persist envelope + master volume from audio/synth.Synth."""
    env = getattr(synth, "env", {})
    data = {
        "type": "synth_settings",
        "master": float(getattr(synth, "master", 0.6)),
        "env": {
            "attack_ms": int(env.get("attack_ms", 5)),
            "decay_ms": int(env.get("decay_ms", 30)),
            "sustain": float(env.get("sustain", 0.7)),
            "release_ms": int(env.get("release_ms", 40)),
        },
    }
    storage.save_json(name, data)


def load_synth_settings(storage, name: str, synth) -> None:
    """Load envelope + master volume into audio/synth.Synth."""
    data = storage.load_json(name)
    if data.get("type") != "synth_settings":
        raise ValueError("Not a synth_settings blob")
    synth.set_volume(float(data["master"]))
    env = data["env"]
    synth.set_envelope(
        attack_ms=int(env["attack_ms"]),
        decay_ms=int(env["decay_ms"]),
        sustain_level=float(env["sustain"]),
        release_ms=int(env["release_ms"]),
    )


# ---------- Sequence I/O (list of {pitch, velocity, duration_ms}) ----------
def save_sequence(storage, name: str, events: list) -> None:
    """Persist a list of note dicts: {pitch, velocity, duration_ms}."""
    norm = []
    for ev in events:
        norm.append({
            "pitch": int(ev["pitch"]),
            "velocity": float(ev.get("velocity", 1.0)),
            "duration_ms": int(ev.get("duration_ms", 200)),
        })
    storage.save_json(name, {"type": "note_sequence", "events": norm})


def load_sequence(storage, name: str) -> list:
    """Load a note sequence previously saved by save_sequence()."""
    data = storage.load_json(name)
    if data.get("type") != "note_sequence":
        raise ValueError("Not a note_sequence blob")
    return list(data["events"])
