# Team Mug — Light Orchestra (Raspberry Pi Pico W)

Turn light into music. A photoresistor feeds an ADC; we map intensity to musical notes and drive a PWM buzzer. Optional switches add play/pause and scale control. There’s also a lightweight Wi-Fi mode so you can trigger tones from another device on the same network.

---
Video Link Demo - https://drive.google.com/file/d/1KTr6eFR7K83wJlsfjKGP5MMws-QpyccM/view?usp=sharing - https://drive.google.com/file/d/1NOr-fIpoPnacQl0EYEGgdjyJ5QuMcFBL/view?usp=sharing
---

## Hardware

- Raspberry Pi **Pico 2WH** (Wi-Fi/BLE, with headers) + Freenove Pico breakout  
- **Photoresistor** + 10 kΩ divider → analog out to an **ADC** pin  
- **Piezo buzzer** (passive) → any **PWM-capable** GPIO + GND  
- 2 × **tactile switches** (optional) → GPIO to GND (internal pull-ups)

**Our wiring (final build):**
- Light sensor → **GP28 / ADC2** (3V3, GND, analog out → GP28)  
- Buzzer → **GP15** (PWM) + GND  
- Switches (SW) → **GP16** and **GP17** to GND (optional; pull-ups enabled in code)

---

## Software Architecture

- **Orchestrator (`audio/orchestrator.py`)**  
  Central loop (~10 ms) that reads the light sensor, handles switches (play/pause, scale, debug), maps intensity to notes, and advances the synth.

- **Mapping (`audio/light_to_note.py`)**  
  Converts light (%) into musical events (MIDI pitch, velocity, duration) across selectable scales and note ranges; configurable at runtime.

- **Synth (`audio/synth.py`)**  
  Mono voice with MIDI→Hz and a lightweight ADSR; non-blocking `tick(now_ms)` updates duty/volume each frame.

- **Sequencer & Storage (`sequencer/`, `storage/`, `integration/`)**  
  Record timestamped note events, loop/quantize playback, and persist/load patterns and synth settings; used by tests and demos.

- **UI (`ui/`)**  
  Small demos and feedback flows that drive record/play and show status; validates debounce and user interactions.

- **Wi-Fi Server (alt run mode)**  
  Async HTTP endpoints to query status and play/stop tones from another device on the LAN; starts muted to avoid boot beeps.  
  *(Some docs say `GET /health` & `POST /stop`; in this branch we use `GET /`, `POST /play_note`, `POST /stop`.)*

- **HAL & Config (`hal/`, `config/`)**  
  Thin, testable drivers around `machine` (ADC/PWM) plus centralized pins/tunables; pop-safe PWM and normalized ADC reads.

---

## What Works Today

- **Laptop (no hardware):**
  - `python -m run_all_tests_unified` runs:
    - Storage/UI tests
    - HAL/Synth/Mapper/Orchestrator coherence tests
    - A combined **Storage↔Audio** test that saves synth settings + a short sequence, reloads them, and *actually drives* the PWM mock (verifies end-to-end).
  - `python -m main_pc` runs the orchestra on desktop time shims.

- **Pico (orchestrator mode):**  
  Light→music works with optional switches: **SW1** tap = play/pause; **SW1** hold = calibrate; **SW2** tap = change scale; **SW2** hold = toggle debug.

- **Pico (Wi-Fi mode):**  
  Device connects (unmuted on boot). Minimal API supports a status page and play/stop via JSON.  
  (Some early docs mention `GET /health`; in this branch we use `GET /` for status plus `POST /play_note` and `POST /stop`.)

---

## What We’d Add With More Time

- Web UI over Wi-Fi (scale/range, record/play, tempo, loop) + on-device Wi-Fi setup page
- Sequence mode over HTTP (upload pattern, tempo & loop control)
- Richer synthesis (polyphony, smoother envelopes) and optional I²S DAC/amp
- UX polish (LED feedback, volume knob), auto-calibration on boot
- Housing - better housing to match requirements of child's toy. Also for a more cohesive cleaner polish.

---

## Team & Roles

### Audio/Synth Lead — *Phyo*
The audio synthesis process of the toy relies mainly on the conversion of MIDI pitches to a frequency in hz. It is also responsible for the master volume of the entire system. The user of the toy would be able to tune and modify the pitch, volume, while the orchestrator file that I made helps with the light-to-music conversion function. The file also calls multiple other files I made, including the switches and the individual sensor files. During the testing phase, I verified that the pitch and volume of the buzzer would be mapped with the output of the midi_to_hz function call thus allowing the user to modify the buzzer as they wish.


### Networking Lead — *Amado*
Our Raspberry Pi based light-buzzer integrator comes with a feature to gather the status or kill the song currently being played through HTTP requests relayed across a common wi-fi network on a separate machine. Ideally, there would be a display interface on the toy box itself that allows the user to configure a wifi SSID and password for the Raspberry Pi to connect to along with a web interface that a user could run through their device that allows the user to send these requests in a user-intuitive manner. However, in its primitive state, the client uses the IP address of a given Raspberry Pi to send a request which is caught in an asynchronous server task on the Raspberry Pi’s side. The request is parsed and a response completes the handshake through a JSON-style message. Our implementation currently supports two request endpoints: GET /health and POST /stop.


### Storage & UI Lead — *Pat*
I built the storage and interface layer of the toy that lets users record, save and replay the musical notes they play through the storing of signals. The toy ensures button presses like record or play are simple and give immediate LED feedback, while musical patterns are safely stored for reuse.

Using both test scripts and demos, I validated scenarios such as saving empty patterns, toggling recording with debounce timing, and ensuring playback matched the stored events. Through testing, I uncovered issues like duplicate button presses being misread or LEDs not signaling errors clearly. I then refined the design , for example, improving debounce handling and expanding LED feedback for error states so that every action gives clear, immediate feedback.


### Sequencer & State Machine Lead — *Juhan*
I built the sequencer and state machine that records light-triggered note events, stores them with timestamps, and plays them back with looping and quantization. I tested it first by simulating events to check timing and playback, then by integrating it with the Controller and Storage modules to confirm that patterns could be saved, loaded, and replayed correctly.


### Hardware Abstraction Layer & Full Software Integration — *Phyliss*
I was in charge of our hardware abstraction layer (HAL) and integration. I focused on making the system reliable, portable, and easy to work on as a team. I standardized the pin/config management (config/pins.py) and implemented the PWM audio driver with pop-safe ordering (mute → set freq → set duty → play → mute) plus safe clamping, alongside the ADC light reader with clean, testable hooks. On top of the HAL, I drove the full software integration: aligning the synth (non-blocking tick loop), light-to-note mapping, and orchestrator timing so they run coherently both on a laptop (with MicroPython shims) and on the Pico. To keep regressions out, I also added a unified test runner that exercises Storage/UI, the HAL↔Synth↔Orchestrator pipeline, and a real Storage↔Audio path. For the Wi-Fi mode, I included a stable continuous playing sound alongside and a pop-safe play path so the networking endpoint can trigger notes without affecting the core loop. Overall, this let every lead stream build against a stable HAL and guaranteed that all pieces run together end-to-end.


### Housing Lead — *Mahnoor*
Designed the enclosure concept and layout to keep wiring clean, switches accessible, and the light sensor exposed for reliable readings, while leaving space for future display/controls.

---

## Setup & Usage

### Note:
Basic pico testing was conducted to ensure hardware piece works beforehand.

### Laptop (development/testing)
cd tests
python -m run_all_tests_unified   # all suites, including Storage↔Audio integration
python -m main_pc                 # desktop run (no hardware)
Pico (orchestrator mode)

Ensure pins in config/pins.py match wiring:
PIN_BUZZER = 15
PIN_LIGHT_ADC = 28

Copy audio/, hal/, config/, etc. to the device root or keep them under /src and add to sys.path in main.py:
import sys
if '/src' not in sys.path: sys.path.append('/src')
Reboot or import main in the REPL.

Hold SW1 to calibrate; SW1 tap = play/pause; SW2 tap = change scale.

Pico (Wi-Fi API mode)
Boot the Wi-Fi main.py and note the printed IP.


From computer (PowerShell example):
$IP="10.0.0.123"
# Play C5 (~523 Hz) for 0.5 s
curl.exe -s -X POST "http://$IP/play_note" -H "Content-Type: application/json" -d "{\"frequency\":523,\"duration\":0.5}"
# Stop
curl.exe -s -X POST "http://$IP/stop" -H "Content-Type: application/json" -d "{}"


Repo Structure (key bits)
src/
  audio/            # synth, orchestrator, light sensor, switches, mapping
  hal/              # PWM/ADC HAL drivers
  config/           # pins & tunables
  storage/, ui/     # storage and UI components + tests
  main_pc.py        # desktop runner
  main.py           # Pico runner (orchestrator or Wi-Fi mode)


