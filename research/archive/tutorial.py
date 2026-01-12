"""
COMPLETE python-osc TUTORIAL
From zero to controlling synthesis parameters

Prerequisites:
    pip install python-osc

What you'll need running to hear results:
    - SuperCollider (easiest - boot the server on default port 57120)
    - OR Pure Data with OSC receive setup
    - OR TouchOSC configured to receive

This tutorial is progressive - each section builds on concepts from previous ones.
"""

import time
from pythonosc import udp_client, dispatcher, osc_server
from pythonosc.osc_message_builder import OscMessageBuilder
import threading

print("=" * 70)
print("PYTHON-OSC TUTORIAL")
print("=" * 70)

# =============================================================================
# SECTION 1: Understanding OSC Messages
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 1: What is an OSC Message?")
print("=" * 70)

"""
An OSC message has two parts:
1. ADDRESS PATTERN - like a URL path: /synth/frequency
2. ARGUMENTS - the data: 440, "hello", 0.5

Think of it like calling a function:
    /synth/play(frequency=440, amplitude=0.5)
"""

print("""
OSC Message Structure:
    Address: /synth/frequency
    Arguments: [440]

This means: "Set the frequency of 'synth' to 440"
""")

# =============================================================================
# SECTION 2: Your First OSC Client (Sending Messages)
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 2: Sending Your First OSC Message")
print("=" * 70)

# Create a client that sends to localhost on port 57120 (SuperCollider default)
client = udp_client.SimpleUDPClient("127.0.0.1", 57120)

print("Created OSC client targeting 127.0.0.1:57120")
print("Sending message: /hello ['world']")

# Send a simple message
client.send_message("/hello", ["world"])

print("Message sent! (If SuperCollider is running, it received it)")
print("\nNote: Nothing happens yet because SC doesn't have a /hello handler")

# =============================================================================
# SECTION 3: Controlling SuperCollider Synths
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 3: Making Sound with SuperCollider")
print("=" * 70)

print("""
SuperCollider Command to create a synth:
    /s_new [synth_name, node_id, add_action, target, arg1_name, arg1_value, ...]

Let's break this down:
    - synth_name: "default" (SC's built-in sine wave)
    - node_id: -1 (let SC assign an ID)
    - add_action: 0 (add to head of group)
    - target: 0 (default group)
    - freq: 440 (frequency in Hz)
    - amp: 0.3 (amplitude 0.0 to 1.0)
""")

input("\nPress ENTER to play a 440Hz tone for 1 second...")

# Play a tone
client.send_message("/s_new", ["default", -1, 0, 0, "freq", 440, "amp", 0.3])
print("Playing 440Hz tone...")
time.sleep(1)

# Stop all synths
client.send_message("/g_freeAll", [0])
print("Stopped")

# =============================================================================
# SECTION 4: Playing Multiple Notes
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 4: Playing a Melody")
print("=" * 70)

melody = [440, 494, 523, 587, 659, 698, 784, 880]  # A4 to A5
note_names = ["A4", "B4", "C5", "D5", "E5", "F5", "G5", "A5"]

input("\nPress ENTER to play a scale...")

for freq, name in zip(melody, note_names):
    print(f"Playing {name} ({freq}Hz)")
    client.send_message("/s_new", ["default", -1, 0, 0, "freq", freq, "amp", 0.2])
    time.sleep(0.3)
    client.send_message("/g_freeAll", [0])
    time.sleep(0.1)

print("Scale complete!")

# =============================================================================
# SECTION 5: Controlling Synth Parameters in Real-Time
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 5: Real-Time Parameter Control")
print("=" * 70)

print("""
We can control a running synth by:
1. Starting it with a specific node ID
2. Sending /n_set messages to change its parameters

Let's create a synth that sweeps from low to high frequency.
""")

input("\nPress ENTER to hear a frequency sweep...")

# Start a synth with node ID 1000
client.send_message("/s_new", ["default", 1000, 0, 0, "freq", 200, "amp", 0.2])
print("Started synth with ID 1000")

# Sweep the frequency
for freq in range(200, 1000, 50):
    client.send_message("/n_set", [1000, "freq", freq])
    print(f"Frequency: {freq}Hz")
    time.sleep(0.1)

# Stop the specific synth
client.send_message("/n_free", [1000])
print("Synth stopped")

# =============================================================================
# SECTION 6: Receiving OSC Messages (Server)
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 6: Receiving OSC Messages")
print("=" * 70)

print("""
So far we've only SENT messages. Now let's RECEIVE them.
This is useful for:
- Building controllers
- Receiving feedback from audio software
- Building two-way communication systems
""")

# Create a dispatcher - routes incoming messages to functions
disp = dispatcher.Dispatcher()


# Define a handler function
def print_handler(address, *args):
    print(f"Received: {address} with args: {args}")


# Map any address to our handler
disp.map("/*", print_handler)

# Create server on port 5005
server = osc_server.ThreadingOSCUDPServer(("127.0.0.1", 5005), disp)
print("OSC Server listening on 127.0.0.1:5005")

# Start server in background thread
server_thread = threading.Thread(target=server.serve_forever)
server_thread.daemon = True
server_thread.start()

print("\nServer is running. Let's send it some messages...")

# Create a client to send TO our own server
test_client = udp_client.SimpleUDPClient("127.0.0.1", 5005)

# Send various messages
test_client.send_message("/test", ["hello"])
time.sleep(0.1)
test_client.send_message("/frequency", [440])
time.sleep(0.1)
test_client.send_message("/synth/play", ["note", 60, "velocity", 100])
time.sleep(0.5)

print("\nServer received the messages above!")

# =============================================================================
# SECTION 7: Building a Simple Sequencer
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 7: Building a Simple 4-Step Sequencer")
print("=" * 70)

sequence = [
    {"freq": 440, "dur": 0.5},
    {"freq": 550, "dur": 0.5},
    {"freq": 660, "dur": 0.5},
    {"freq": 440, "dur": 0.5},
]

print("Sequence pattern: A4 - C#5 - E5 - A4")
input("\nPress ENTER to play the sequence twice...")

for loop in range(2):
    print(f"\nLoop {loop + 1}")
    for step, note in enumerate(sequence):
        print(f"  Step {step + 1}: {note['freq']}Hz")
        client.send_message("/s_new", ["default", -1, 0, 0,
                                       "freq", note['freq'],
                                       "amp", 0.2])
        time.sleep(note['dur'])
        client.send_message("/g_freeAll", [0])
        time.sleep(0.05)

print("\nSequencer demo complete!")

# =============================================================================
# SECTION 8: Advanced - Bundles (Timed Messages)
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 8: OSC Bundles - Perfectly Timed Messages")
print("=" * 70)

print("""
OSC Bundles let you send multiple messages with precise timing.
All messages in a bundle are executed at the exact same time.
This is crucial for tight musical timing.
""")

from pythonosc import osc_bundle_builder

input("\nPress ENTER to play a chord using a bundle...")

# Create a bundle
bundle = osc_bundle_builder.OscBundleBuilder(
    osc_bundle_builder.IMMEDIATELY
)

# Add three notes to the bundle (a major chord: A-C#-E)
bundle.add_content(
    OscMessageBuilder(address="/s_new").add_arg("default").add_arg(-1)
    .add_arg(0).add_arg(0).add_arg("freq").add_arg(440).add_arg("amp").add_arg(0.15).build()
)
bundle.add_content(
    OscMessageBuilder(address="/s_new").add_arg("default").add_arg(-1)
    .add_arg(0).add_arg(0).add_arg("freq").add_arg(554.37).add_arg("amp").add_arg(0.15).build()
)
bundle.add_content(
    OscMessageBuilder(address="/s_new").add_arg("default").add_arg(-1)
    .add_arg(0).add_arg(0).add_arg("freq").add_arg(659.25).add_arg("amp").add_arg(0.15).build()
)

# Send the bundle
sub_bundle = bundle.build()
client._sock.sendto(sub_bundle.dgram, ("127.0.0.1", 57120))

print("Playing A major chord (A-C#-E)")
time.sleep(2)
client.send_message("/g_freeAll", [0])

# =============================================================================
# SECTION 9: Working with Custom Data Types
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 9: OSC Data Types")
print("=" * 70)

print("""
OSC supports multiple data types:
- int: whole numbers
- float: decimals
- string: text
- blob: binary data
- True/False: booleans

Python-osc automatically handles type conversion.
""")

# Test different data types with our server
print("\nSending different data types to our server:")
test_client.send_message("/int", [42])
time.sleep(0.1)
test_client.send_message("/float", [3.14159])
time.sleep(0.1)
test_client.send_message("/string", ["Hello OSC"])
time.sleep(0.1)
test_client.send_message("/bool", [True])
time.sleep(0.1)
test_client.send_message("/mixed", [1, 2.5, "three", True])
time.sleep(0.5)

# =============================================================================
# SECTION 10: Building a Pattern-Based Composition System
# =============================================================================
print("\n" + "=" * 70)
print("SECTION 10: Pattern-Based Composition")
print("=" * 70)

print("""
Now let's combine everything into a simple composition system.
This is the foundation for tools like Sardine.
""")


class Pattern:
    def __init__(self, values, durations):
        self.values = values
        self.durations = durations
        self.index = 0

    def next(self):
        val = self.values[self.index % len(self.values)]
        dur = self.durations[self.index % len(self.durations)]
        self.index += 1
        return val, dur


# Define patterns
melody_pattern = Pattern(
    values=[440, 494, 523, 440, 392, 440],  # frequencies
    durations=[0.25, 0.25, 0.5, 0.25, 0.25, 0.5]  # note lengths
)

bass_pattern = Pattern(
    values=[220, 220, 196, 196],  # bass notes (octave lower)
    durations=[1.0, 1.0, 1.0, 1.0]
)

print("Composition: Simple melody with bass line")
print("Melody pattern: 6 notes")
print("Bass pattern: 4 notes (they'll cycle at different rates)")

input("\nPress ENTER to play the composition...")

# Play for 16 beats
for beat in range(16):
    # Get next melody note
    mel_freq, mel_dur = melody_pattern.next()

    # Play melody
    client.send_message("/s_new", ["default", -1, 0, 0,
                                   "freq", mel_freq,
                                   "amp", 0.15])

    # On beat 1 of every 4, play bass note
    if beat % 4 == 0:
        bass_freq, bass_dur = bass_pattern.next()
        client.send_message("/s_new", ["default", -1, 0, 0,
                                       "freq", bass_freq,
                                       "amp", 0.2])

    time.sleep(mel_dur)
    client.send_message("/g_freeAll", [0])

print("\nComposition complete!")

# =============================================================================
# CONCLUSION
# =============================================================================
print("\n" + "=" * 70)
print("TUTORIAL COMPLETE!")
print("=" * 70)

print("""
You've learned:
✓ OSC message structure (address + arguments)
✓ Sending messages to SuperCollider
✓ Controlling synth parameters in real-time
✓ Receiving OSC messages (building servers)
✓ Creating sequences and patterns
✓ OSC bundles for precise timing
✓ Working with different data types
✓ Building a simple composition system

NEXT STEPS:
1. Experiment with these examples
2. Try controlling Pure Data or TouchOSC
3. Build your own patterns and sequences
4. Explore Sardine (which does all this with better syntax)
5. Create a composition database_v1 system

Key Resources:
- python-osc docs: https://python-osc.readthedocs.io
- SuperCollider docs: https://doc.sccode.org
- Sardine: https://github.com/Bubobubobubobubo/sardine

Happy live coding!
""")

# Cleanup
server.shutdown()
print("\nServer stopped. Tutorial finished.")