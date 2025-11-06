#!/usr/bin/env python3
"""
Christmas Piano Lights Controller (RTMidi version)
Controls 8-channel relay board via Raspberry Pi GPIO pins based on MIDI input from piano.
"""

import time
from typing import Set
import rtmidi
import RPi.GPIO as GPIO

class PianoLightsController:
    def __init__(self):
        # GPIO pins for 8-channel relay board
        self.relay_pins = [18, 19, 20, 21, 22, 23, 24, 25]

        # Setup note-to-relay mapping
        self.setup_note_mapping()

        # Track which notes are currently pressed
        self.active_notes: Set[int] = set()

        # MIDI setup
        self.midi_input = None
        self.running = False

        self.setup_gpio()
        self.setup_midi()

    def setup_note_mapping(self):
        """Setup mapping from MIDI notes to relay channels."""
        self.note_to_relay = {}

        # Music-focused mapping - more relays for commonly used notes
        # Distribution based on typical music usage patterns
        octave_ranges = [
            (21, 47),   # A0-B2 (bass) -> Relay 0 (27 keys)
            (48, 53),   # C3-F3 -> Relay 1 (6 keys)
            (54, 59),   # F#3-B3 -> Relay 2 (6 keys)
            (60, 65),   # C4-F4 (Middle C region) -> Relay 3 (6 keys)
            (66, 71),   # F#4-B4 -> Relay 4 (6 keys)
            (72, 77),   # C5-F5 -> Relay 5 (6 keys)
            (78, 83),   # F#5-B5 -> Relay 6 (6 keys)
            (84, 108),  # C6-C8 (treble) -> Relay 7 (25 keys)
        ]

        for relay_channel, (start_note, end_note) in enumerate(octave_ranges):
            for note in range(start_note, end_note + 1):
                self.note_to_relay[note] = relay_channel

        print(f"Octave mapping loaded: {len(self.note_to_relay)} keys mapped to 8 relays")

    def setup_gpio(self):
        """Initialize GPIO pins for relay control."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup relay pins as outputs, initially HIGH (relays off for active-low boards)
        for pin in self.relay_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)  # Most relay boards are active-low

        print(f"GPIO initialized for pins: {self.relay_pins}")

    def setup_midi(self):
        """Initialize MIDI input using RTMidi."""
        self.midi_input = rtmidi.MidiIn()

        # List available MIDI ports
        available_ports = self.midi_input.get_ports()
        print("Available MIDI ports:")
        for i, port in enumerate(available_ports):
            print(f"  {i}: {port}")

        if not available_ports:
            raise Exception("No MIDI input ports found!")

        # Find Casio port or use first available
        casio_port = None
        for i, port in enumerate(available_ports):
            if 'casio' in port.lower() or 'ctk' in port.lower():
                casio_port = i
                break

        if casio_port is not None:
            self.midi_input.open_port(casio_port)
            print(f"Connected to MIDI port: {available_ports[casio_port]}")
        else:
            # Use first available port
            self.midi_input.open_port(0)
            print(f"Connected to MIDI port: {available_ports[0]}")

        # Set callback for MIDI messages
        self.midi_input.set_callback(self.midi_callback)

    def midi_callback(self, event, data=None):
        """Handle incoming MIDI messages."""
        message, deltatime = event

        if len(message) >= 3:
            status = message[0]
            note = message[1]
            velocity = message[2]

            # Note On (0x90-0x9F) or Note Off (0x80-0x8F)
            if 0x80 <= status <= 0x8F:  # Note Off
                self.handle_note_off(note)
            elif 0x90 <= status <= 0x9F:  # Note On
                if velocity == 0:  # Note On with velocity 0 = Note Off
                    self.handle_note_off(note)
                else:
                    self.handle_note_on(note, velocity)

    def set_relay(self, relay_channel: int, state: bool):
        """Control a specific relay channel."""
        if 0 <= relay_channel < len(self.relay_pins):
            pin = self.relay_pins[relay_channel]
            # Most relay boards are active-low (LOW = ON, HIGH = OFF)
            GPIO.output(pin, GPIO.LOW if state else GPIO.HIGH)
            print(f"Relay {relay_channel + 1} {'ON' if state else 'OFF'}")

    def handle_note_on(self, note: int, velocity: int):
        """Handle MIDI note on event."""
        if note in self.note_to_relay and velocity > 0:
            relay_channel = self.note_to_relay[note]
            self.active_notes.add(note)
            self.set_relay(relay_channel, True)
            print(f"Note ON: {note} (velocity: {velocity}) -> Relay {relay_channel + 1}")

    def handle_note_off(self, note: int):
        """Handle MIDI note off event."""
        if note in self.note_to_relay and note in self.active_notes:
            relay_channel = self.note_to_relay[note]
            self.active_notes.discard(note)
            self.set_relay(relay_channel, False)
            print(f"Note OFF: {note} -> Relay {relay_channel + 1}")

    def run(self):
        """Main event loop."""
        self.running = True
        print("Piano Lights Controller started. Press Ctrl+C to stop.")
        print(f"Mapped notes: {list(self.note_to_relay.keys())}")

        try:
            while self.running:
                time.sleep(0.1)  # Keep the program running

        except KeyboardInterrupt:
            print("\nShutting down...")

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        self.running = False

        # Turn off all relays
        for i in range(len(self.relay_pins)):
            self.set_relay(i, False)

        # Cleanup GPIO
        GPIO.cleanup()

        # Close MIDI
        if self.midi_input:
            self.midi_input.close_port()

        print("Cleanup complete.")

def main():
    """Main entry point."""
    try:
        controller = PianoLightsController()
        controller.run()
    except Exception as e:
        print(f"Error: {e}")
        GPIO.cleanup()

if __name__ == "__main__":
    main()