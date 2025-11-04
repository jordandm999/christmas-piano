#!/usr/bin/env python3
"""
Christmas Piano Lights Controller
Controls 8-channel relay board via Raspberry Pi GPIO pins based on MIDI input from piano.
"""

import time
import os
import threading
from typing import Dict, Set

# Disable audio to avoid ALSA errors
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame.midi
import RPi.GPIO as GPIO

class PianoLightsController:
    def __init__(self):
        # GPIO pins for 8-channel relay board (adjust based on your wiring)
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
        # Choose your mapping strategy:

        # STRATEGY 1: Octave Groups (recommended for 88 keys)
        # Each relay controls roughly 11 keys (88 keys / 8 relays)
        # A0(21) to C8(108) = 88 keys total
        self.note_to_relay = {}

        # Octave-based mapping:
        # Relay 0: A0-A#1   (notes 21-34)  - 14 keys
        # Relay 1: B1-B2    (notes 35-47)  - 13 keys
        # Relay 2: C3-B3    (notes 48-59)  - 12 keys
        # Relay 3: C4-B4    (notes 60-71)  - 12 keys (middle octave)
        # Relay 4: C5-B5    (notes 72-83)  - 12 keys
        # Relay 5: C6-B6    (notes 84-95)  - 12 keys
        # Relay 6: C7-B7    (notes 96-107) - 12 keys
        # Relay 7: C8       (note 108)     - 1 key

        octave_ranges = [
            (21, 34),   # A0-A#1 -> Relay 0
            (35, 47),   # B1-B2  -> Relay 1
            (48, 59),   # C3-B3  -> Relay 2
            (60, 71),   # C4-B4  -> Relay 3 (middle)
            (72, 83),   # C5-B5  -> Relay 4
            (84, 95),   # C6-B6  -> Relay 5
            (96, 107),  # C7-B7  -> Relay 6
            (108, 108), # C8     -> Relay 7
        ]

        for relay_channel, (start_note, end_note) in enumerate(octave_ranges):
            for note in range(start_note, end_note + 1):
                self.note_to_relay[note] = relay_channel

        print(f"Octave mapping loaded: {len(self.note_to_relay)} keys mapped to 8 relays")

        # ALTERNATIVE STRATEGIES (uncomment to use):

        # STRATEGY 2: Equal key groups (11 keys per relay)
        # self.note_to_relay = {}
        # keys_per_relay = 11
        # for note in range(21, 109):  # A0 to C8
        #     relay_channel = min((note - 21) // keys_per_relay, 7)
        #     self.note_to_relay[note] = relay_channel

        # STRATEGY 3: White keys only (7 relays for C-B, 1 for all black keys)
        # white_key_pattern = [0, 2, 4, 5, 7, 9, 11]  # C, D, E, F, G, A, B
        # self.note_to_relay = {}
        # for note in range(21, 109):
        #     note_in_octave = note % 12
        #     if note_in_octave in white_key_pattern:
        #         relay_channel = white_key_pattern.index(note_in_octave)
        #     else:
        #         relay_channel = 7  # All black keys -> Relay 7
        #     self.note_to_relay[note] = relay_channel

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
        """Initialize MIDI input."""
        pygame.midi.init()

        # List available MIDI devices
        print("Available MIDI devices:")
        for i in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(i)
            print(f"  {i}: {info[1].decode()} - {'Input' if info[2] else 'Output'}")

        # Find first MIDI input device
        midi_input_id = None
        for i in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(i)
            if info[2]:  # is input
                midi_input_id = i
                break

        if midi_input_id is None:
            raise Exception("No MIDI input device found!")

        self.midi_input = pygame.midi.Input(midi_input_id)
        print(f"MIDI input initialized: {pygame.midi.get_device_info(midi_input_id)[1].decode()}")

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

    def process_midi_events(self):
        """Process incoming MIDI events."""
        if self.midi_input.poll():
            midi_events = self.midi_input.read(10)

            for event in midi_events:
                data = event[0]
                status = data[0]
                note = data[1]
                velocity = data[2] if len(data) > 2 else 0

                # Note On (0x90-0x9F) or Note Off (0x80-0x8F)
                if 0x80 <= status <= 0x8F:  # Note Off
                    self.handle_note_off(note)
                elif 0x90 <= status <= 0x9F:  # Note On
                    if velocity == 0:  # Note On with velocity 0 = Note Off
                        self.handle_note_off(note)
                    else:
                        self.handle_note_on(note, velocity)

    def run(self):
        """Main event loop."""
        self.running = True
        print("Piano Lights Controller started. Press Ctrl+C to stop.")
        print(f"Mapped notes: {list(self.note_to_relay.keys())}")

        try:
            while self.running:
                self.process_midi_events()
                time.sleep(0.001)  # Small delay to prevent excessive CPU usage

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
            self.midi_input.close()
        pygame.midi.quit()

        print("Cleanup complete.")

def main():
    """Main entry point."""
    try:
        controller = PianoLightsController()
        controller.run()
    except Exception as e:
        print(f"Error: {e}")
        GPIO.cleanup()
        pygame.midi.quit()

if __name__ == "__main__":
    main()