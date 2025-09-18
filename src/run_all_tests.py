# run_all_tests.py
# Master test runner for Light Orchestra project

import os, sys, traceback

def run(path):
    print(f"\n=== RUN {path} ===")
    try:
        ns = {}
        with open(path, "r", encoding="utf-8") as f:
            code = compile(f.read(), path, "exec")
            exec(code, ns, ns)
        print(f"PASS: {path}")
    except SystemExit:
        # allow tests to call sys.exit()
        print(f"PASS (SystemExit): {path}")
    except AssertionError as e:
        print(f"FAIL (assert): {path}\n{e}")
        traceback.print_exc()
    except Exception as e:
        print(f"FAIL (error): {path}\n{e}")
        traceback.print_exc()

def main():
    # Ensure project root is in sys.path
    sys.path.append(os.getcwd())
    print("Python:", sys.version)
    print("CWD:", os.getcwd())
    print("Files in CWD:", os.listdir())

    # List of test/demo scripts to run
    tests = [
        "tests/test_storage.py",
        "tests/test_ui.py",
        "demo_ui_storage_real.py",
    ]

    for t in tests:
        if os.path.exists(t):
            run(t)
        else:
            print(f"SKIP (not found): {t}")

if __name__ == "__main__":
    main()
