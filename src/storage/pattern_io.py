# storage/pattern_io.py
# JSON-backed store for patterns. Safe-writes, name sanitization, and corruption handling.

try:
    import ujson as json
except Exception:
    import json

import os

# MicroPython compatibility
try:
    from time import ticks_ms  # type: ignore
except Exception:
    import time
    ticks_ms = lambda: int(time.time() * 1000)  # noqa: E731

DEFAULT_DIR = "/patterns"

def _ensure_dir(path: str):
    try:
        os.listdir(path)
    except OSError:
        try:
            os.mkdir(path)
        except OSError:
            # If nested paths used, attempt to create recursively (CPython)
            if hasattr(os, "makedirs"):
                os.makedirs(path, exist_ok=True)

def _sanitize_name(name: str) -> str:
    # Allow letters, digits, dash, underscore; replace others with underscore.
    safe = []
    for c in name.strip():
        if c.isalnum() or c in ("-", "_"):
            safe.append(c)
        else:
            safe.append("_")
    out = "".join(safe).strip("_")
    return out or "untitled"

class PatternStore:
    def __init__(self, base_dir: str = DEFAULT_DIR, max_bytes: int | None = None):
        self.base_dir = base_dir
        self.max_bytes = max_bytes
        _ensure_dir(self.base_dir)

    def _path_for(self, name: str) -> str:
        return f"{self.base_dir}/{_sanitize_name(name)}.json"

    def list_patterns(self) -> list[str]:
        try:
            files = os.listdir(self.base_dir)
        except OSError:
            return []
        names = []
        for f in files:
            if f.endswith(".json"):
                names.append(f[:-5])
        names.sort()
        return names

    def delete(self, name: str) -> None:
        p = self._path_for(name)
        try:
            os.remove(p)
        except OSError:
            pass

    def save(self, name: str, metadata: dict, events: list) -> None:
        if not isinstance(events, list) or len(events) == 0:
            raise ValueError("Cannot save empty pattern (no events).")
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a dict.")

        payload = {
            "version": 1,
            "saved_ms": ticks_ms(),
            "metadata": metadata,
            "events": events,  # already in compact row form [[t,ch,mag,pitch,dur], ...]
        }
        data = json.dumps(payload)

        if self.max_bytes is not None and len(data) > self.max_bytes:
            raise OSError("Pattern too large for storage limit.")

        _ensure_dir(self.base_dir)
        final = self._path_for(name)
        tmp = final + ".tmp"

        # Safe write: write tmp -> flush -> rename
        try:
            with open(tmp, "w") as fh:
                fh.write(data)
                try:
                    fh.flush()
                    if hasattr(os, "fsync"):
                        os.fsync(fh.fileno())
                except Exception:
                    pass
            # On MicroPython, os.replace may not exist; use remove+rename
            try:
                if hasattr(os, "replace"):
                    os.replace(tmp, final)
                else:
                    try:
                        os.remove(final)
                    except OSError:
                        pass
                    os.rename(tmp, final)
            finally:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
        except OSError as e:
            # Best-effort cleanup
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise e

    def load(self, name: str):
        p = self._path_for(name)
        try:
            with open(p, "r") as fh:
                txt = fh.read()
        except OSError:
            raise FileNotFoundError(f"Pattern '{name}' not found.")
        try:
            obj = json.loads(txt)
        except Exception:
            raise IOError("Corrupt pattern file (invalid JSON).")
        # Validate minimally
        if not isinstance(obj, dict) or "events" not in obj or "metadata" not in obj:
            raise IOError("Corrupt pattern file (missing keys).")
        if not isinstance(obj["events"], list):
            raise IOError("Corrupt pattern file (events not list).")
        return obj.get("metadata", {}), obj["events"]
