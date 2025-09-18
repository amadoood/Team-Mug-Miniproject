# orchestrator.py
"""
Light Orchestra Orchestrator
Main control system that coordinates light sensing, audio synthesis, and user controls.
Requires:
  - config/pins.py
  - hal/pwm_audio.py
  - synth.py
  - light_sensor.py
  - switches.py
  - light_to_note.py
"""

import time
from config.pins import PIN_BUZZER, LOOP_PERIOD_MS
from hal.pwm_audio import PWMAudio
from .synth import Synth
from .light_sensor import LightSensor
from .switches import SwitchController
from .light_to_note import LightToNoteMapper


class LightOrchestra:
    """
    Coordinates all hardware components and manages the light-to-music conversion.
    """

    SCALES = ["chromatic", "major", "minor", "pentatonic", "blues", "dorian"]

    def __init__(self, *, audio_pin: int = PIN_BUZZER, light_pin: int = 28, switch_pins=(16, 17)):
        """
        Args:
            audio_pin: GPIO pin for piezo buzzer
            light_pin: ADC pin for light sensor
            switch_pins: GPIO pins for tactile switches (sw_1, sw_2)
        """
        print("Initializing Light Orchestra...")

        # Hardware components
        self.pwm_audio = PWMAudio(audio_pin)
        self.synth = Synth(self.pwm_audio, vol_default=0.6)
        self.light_sensor = LightSensor(light_pin)
        self.switches = SwitchController(list(switch_pins))

        # Mapping system
        self.mapper = LightToNoteMapper(min_note=48, max_note=84, scale="pentatonic")

        # System state
        self.running = False
        self.paused = False
        self.current_light = 0.0      # percent (0..100)
        self.current_note = None
        self.last_note_time = 0
        self.min_note_interval_ms = 100  # Minimum time between new notes

        # Configuration
        self.sensitivity = 1.0  # Light sensitivity multiplier
        self.auto_play = True   # Automatically play notes based on light
        self.debug_output = True

        # Performance settings
        self.tick_interval_ms = int(LOOP_PERIOD_MS)
        self.light_read_interval_ms = 50
        self.last_light_read = 0

        print("Light Orchestra initialized successfully")

    # ---------- User controls ----------
    def calibrate_light_sensor(self):
        """Calibrate the light sensor for current environment."""
        print("\n=== LIGHT SENSOR CALIBRATION ===")
        self.light_sensor.calibrate()
        print("Calibration complete!\n")

    def set_scale(self, scale_name: str):
        """Change musical scale."""
        self.mapper.set_scale(scale_name)
        if self.debug_output:
            print(f"Scale changed to: {scale_name}")

    def set_note_range(self, min_note: int, max_note: int):
        """Set the MIDI note range."""
        self.mapper.set_range(min_note, max_note)
        if self.debug_output:
            print(f"Note range: {min_note} to {max_note}")

    def handle_switch_events(self):
        """Process tactile switch events."""
        events = self.switches.get_events()
        # ensure expected keys exist (defensive, but no try/except for imports)
        for k in ("pressed", "held", "released"):
            events.setdefault(k, [])

        # Switch 1: Play/Pause toggle
        if "sw_1" in events["pressed"]:
            self.paused = not self.paused
            if self.paused:
                self.synth.all_notes_off()
                print("⏸ Paused")
            else:
                print("▶ Resumed")

        # Switch 1 held: Calibrate light sensor
        if "sw_1" in events["held"]:
            self.synth.all_notes_off()
            self.calibrate_light_sensor()

        # Switch 2: Cycle through scales
        if "sw_2" in events["pressed"]:
            cur = getattr(self.mapper, "scale", self.SCALES[0])
            try:
                idx = self.SCALES.index(cur)
            except ValueError:
                idx = 0
            next_scale = self.SCALES[(idx + 1) % len(self.SCALES)]
            self.set_scale(next_scale)

        # Switch 2 held: Toggle debug output
        if "sw_2" in events["held"]:
            self.debug_output = not self.debug_output
            print(f"Debug output: {'ON' if self.debug_output else 'OFF'}")

    # ---------- Light path ----------
    @staticmethod
    def _clamp(x: float, lo: float, hi: float) -> float:
        return lo if x < lo else hi if x > hi else x

    def _read_light_percent(self) -> float:
        """
        Return light as percentage (0..100).
        Prefers LightSensor.read_intensity(); falls back to normalized read().
        """
        if hasattr(self.light_sensor, "read_intensity"):
            return float(self.light_sensor.read_intensity())
        val = float(self.light_sensor.read())
        return 100.0 * self._clamp(val, 0.0, 1.0)

    def update_light_reading(self, now_ms: int):
        """Update light sensor reading with rate limiting (wrap-safe)."""
        if time.ticks_diff(now_ms, self.last_light_read) >= self.light_read_interval_ms:
            self.current_light = self._read_light_percent()
            self.last_light_read = now_ms

    def process_light_to_music(self, now_ms: int):
        """Convert current light reading to musical output."""
        if self.paused or not self.auto_play:
            return

        adjusted_light = self._clamp(self.current_light * self.sensitivity, 0.0, 100.0)

        # Only trigger new notes if minimum interval has passed
        if time.ticks_diff(now_ms, self.last_note_time) < self.min_note_interval_ms:
            return

        # Create & play note event (threshold to avoid noise)
        if adjusted_light > 5.0:
            note_event = self.mapper.create_note_event(adjusted_light)
            self.synth.note_on(
                note_event["pitch"],
                velocity=note_event["velocity"],
                duration_ms=note_event["duration_ms"],
                now_ms=now_ms,
            )
            self.current_note = note_event
            self.last_note_time = now_ms

            if self.debug_output:
                print(
                    "♪ Light: {:.1f}% → Note: {} (vel: {:.2f}, dur: {} ms)".format(
                        adjusted_light,
                        note_event["pitch"],
                        note_event["velocity"],
                        note_event["duration_ms"],
                    )
                )

    # ---------- Status ----------
    def print_status(self):
        """Print current system status."""
        light_debug = self.light_sensor.get_debug_info()
        scale_info = self.mapper.get_scale_info()

        print("\n=== LIGHT ORCHESTRA STATUS ===")
        print(f"Running: {self.running}, Paused: {self.paused}")
        print(f"Light: {self.current_light:.1f}% (raw: {light_debug['raw']}, voltage: {light_debug['voltage']}V)")
        print(f"Scale: {scale_info['scale']} ({scale_info['available_notes']} notes)")
        print(f"Current note: {self.current_note['pitch'] if self.current_note else 'None'}")
        active_switches = self.switches.get_pressed_switches()
        print(f"Active switches: {active_switches if active_switches else 'None'}")
        print("Controls: SW1=Play/Pause(hold=calibrate), SW2=Scale(hold=debug)")
        print("===========================\n")

    # ---------- Main loop ----------
    def run(self):
        """Main orchestrator loop."""
        print("Starting Light Orchestra...")
        print("Controls:")
        print("  SW1: Play/Pause (hold for light calibration)")
        print("  SW2: Change scale (hold to toggle debug)")
        print("  Ctrl+C: Stop\n")

        self.running = True
        last_status_print = 0
        status_interval_ms = 5000  # Print status every 5 seconds

        try:
            while self.running:
                now_ms = time.ticks_ms()

                # Update all input components
                self.switches.update()
                self.update_light_reading(now_ms)

                # Process events and control logic
                self.handle_switch_events()
                self.process_light_to_music(now_ms)

                # Update audio synthesis (envelope, etc.)
                self.synth.tick(now_ms)

                # Periodic status output
                if self.debug_output and time.ticks_diff(now_ms, last_status_print) >= status_interval_ms:
                    self.print_status()
                    last_status_print = now_ms

                # Maintain loop timing
                time.sleep_ms(self.tick_interval_ms)

        except KeyboardInterrupt:
            print("\nStopping Light Orchestra...")
        finally:
            self.stop()

    def stop(self):
        """Clean shutdown of all components."""
        self.running = False
        self.synth.all_notes_off()
        self.pwm_audio.stop()
        print("Light Orchestra stopped.")

    # ---------- Component test ----------
    def test_components(self):
        """Test all hardware components quickly."""
        print("\n=== COMPONENT TEST ===")

        # Test light sensor
        print("Testing light sensor...")
        for i in range(5):
            light = self._read_light_percent()
            debug_info = self.light_sensor.get_debug_info()
            print(f"  Light {i+1}: {light:.1f}% (raw: {debug_info['raw']})")
            time.sleep_ms(500)

        # Test audio synthesis
        print("Testing audio synthesis...")
        test_notes = [60, 64, 67, 72]  # C major chord
        for note in test_notes:
            print(f"  Playing MIDI note {note}")
            self.synth.note_on(note, velocity=0.7, duration_ms=300, now_ms=time.ticks_ms())

            # Run synth envelope for note duration
            start_time = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start_time) < 400:
                self.synth.tick(time.ticks_ms())
                time.sleep_ms(10)

        # Test switches
        print("Testing switches (press any switch within 5 seconds)...")
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 5000:
            self.switches.update()
            events = self.switches.get_events()
            if events.get("pressed"):
                print(f"  Switch pressed: {events['pressed']}")
            time.sleep_ms(50)

        print("Component test complete!\n")
