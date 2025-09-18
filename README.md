# 2025 Fall ECE Senior Design Miniproject

## Design

### Audio/Syth Lead - Phyo 

The audio synthesis process of the toy relies mainly on the conversion of MIDI pitches to a frequency in hz. It is also responsible for the master volume of the entire system. The user of the toy would be able to tune and modify the pitch, volume, while the orchestrator file that I made helps with the light-to-music conversion function. The file also calls multiple other files I made, including the switches and the individual sensor files. During the testing phase, I verified that the pitch and volume of the buzzer would be mapped with the output of the midi_to_hz function call thus allowing the user to modify the buzzer as they wish. 

### Networking Lead - Amado 

Our Raspberry Pi based light-buzzer integrator comes with a feature to gather the status or kill the song currently being played through HTTP requests relayed across a common wi-fi network on a separate machine. Ideally, there would be a display interface on the toy box itself that allows the user to configure a wifi SSID and password for the Raspberry Pi to connect to along with a web interface that a user could run through their device that allows the user to send these requests in a user-intuitive manner. However, in its primitive state, the client uses the IP address of a given Raspberry Pi to send a request which is caught in an asynchronous server task on the Raspberry Pi’s side. The request is parsed and a response completes the handshake through a JSON-style message. Our implementation currently supports two request endpoints: GET /health and POST /stop.

### Storage & UI Lead - Pat

I built the storage and interface layer of the toy that lets users record, save and replay the musical notes they play through the storing of signals. The toy ensures button presses like record or play are simple and give immediate LED feedback, while musical patterns are safely stored for reuse.

Using both test scripts and demos, I validated scenarios such as saving empty patterns, toggling recording with debounce timing, and ensuring playback matched the stored events. Through testing, I uncovered issues like duplicate button presses being misread or LEDs not signaling errors clearly. I then refined the design , for example, improving debounce handling and expanding LED feedback for error states so that every action gives clear, immediate feedback.

### Sequencer & State Machine Lead – Juhan

I built the sequencer and state machine that records light-triggered note events, stores them with timestamps, and plays them back with looping and quantization. I tested it first by simulating events to check timing and playback, then by integrating it with the Controller and Storage modules to confirm that patterns could be saved, loaded, and replayed correctly.
