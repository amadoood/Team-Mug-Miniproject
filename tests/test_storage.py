# tests/test_storage.py
import os
from storage.pattern_io import PatternStore
from models.types import NoteEvent

TEST_DIR = "./patterns_test"

def _clean():
    try:
        for f in os.listdir(TEST_DIR):
            os.remove(TEST_DIR + "/" + f)
        os.rmdir(TEST_DIR)
    except Exception:
        pass

def run_tests():
    print("== Storage tests ==")
    _clean()
    store = PatternStore(TEST_DIR)

    # 1. Sunny save+load
    events = [NoteEvent(0, i*100, 0.9, 60+i).to_row() for i in range(5)]
    store.save("My Song:1", {"bpm": 120, "channels": 1}, events)
    names = store.list_patterns()
    assert names == ["My_Song_1"], f"names: {names}"
    meta, rows = store.load("My_Song_1")
    assert len(rows) == 5 and meta["bpm"] == 120

    # 2. Empty events -> ValueError
    try:
        store.save("bad", {"bpm": 120}, [])
        assert False, "Expected ValueError for empty events"
    except ValueError:
        pass

    # 3. Corrupt file detection
    p = store._path_for("corrupt")
    with open(p, "w") as fh:
        fh.write("{not json}")
    try:
        store.load("corrupt")
        assert False, "Expected IOError for corrupt"
    except IOError:
        pass

    # 4. Delete + list
    store.save("another", {"bpm": 90, "channels": 1}, events[:2])
    assert set(store.list_patterns()) == {"My_Song_1", "another"}
    store.delete("another")
    assert store.list_patterns() == ["My_Song_1"]

    print("All storage tests passed.")
    _clean()

if __name__ == "__main__":
    run_tests()
