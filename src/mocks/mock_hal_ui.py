# mocks/mock_hal_ui.py
class MockUI:
    def __init__(self):
        self.led = {"REC": False, "PLAY": False, "ERR": False, "SAVE": False, "LOAD": False}
        self.log = []  # (action, name, value)

    def set_led(self, name: str, on: bool):
        self.led[name] = bool(on)
        self.log.append(("LED", name, on))

    def flash(self, name: str, times: int = 1):
        for _ in range(times):
            self.set_led(name, True)
            self.set_led(name, False)
