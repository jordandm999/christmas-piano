#!/usr/bin/env python3
"""
Christmas Piano Lights Random Sequence Controller - TEST VERSION
This version mocks GPIO for testing on non-Raspberry Pi systems
"""

import time
import random
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Mock GPIO class for testing
class MockGPIO:
    BCM = "BCM"
    OUT = "OUT"
    HIGH = True
    LOW = False

    @staticmethod
    def setmode(mode):
        logger.debug(f"[GPIO] Set mode: {mode}")

    @staticmethod
    def setwarnings(state):
        logger.debug(f"[GPIO] Set warnings: {state}")

    @staticmethod
    def setup(pin, mode):
        logger.debug(f"[GPIO] Setup pin {pin} as {mode}")

    @staticmethod
    def output(pin, state):
        # This is where the actual relay control would happen
        state_str = "HIGH (OFF)" if state else "LOW (ON)"
        logger.debug(f"[GPIO] Pin {pin} -> {state_str}")

    @staticmethod
    def cleanup():
        logger.debug("[GPIO] Cleanup called")

GPIO = MockGPIO()

class ChristmasLightsController:
    def __init__(self):
        # GPIO pins for relay board
        self.relay_pins = [18, 19, 20, 21, 22, 23, 24]

        # Pin groups for Sequence 1
        self.groups = [
            [18, 19],
            [20, 21],
            [22, 23, 24]
        ]

        # Timezone for MST
        self.timezone = ZoneInfo('America/Denver')

        # Active hours (5pm to 11:59pm)
        self.start_hour = 17  # 5pm
        self.end_hour = 23    # 11pm
        self.end_minute = 59  # 11:59pm

        self.running = False
        self.setup_gpio()

    def setup_gpio(self):
        """Initialize GPIO pins for relay control."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup relay pins as outputs, initially HIGH (relays off for active-low boards)
        for pin in self.relay_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)  # Most relay boards are active-low

        logger.info(f"GPIO initialized for pins: {self.relay_pins}")

    def set_pin(self, pin: int, state: bool):
        """Control a specific pin (relay)."""
        # Most relay boards are active-low (LOW = ON, HIGH = OFF)
        GPIO.output(pin, GPIO.LOW if state else GPIO.HIGH)
        logger.debug(f"Pin {pin} set to {'ON' if state else 'OFF'}")

    def set_multiple_pins(self, pins: list, state: bool):
        """Control multiple pins simultaneously."""
        for pin in pins:
            self.set_pin(pin, state)
        logger.info(f"Pins {pins} set to {'ON' if state else 'OFF'}")

    def all_pins_off(self):
        """Turn off all pins."""
        self.set_multiple_pins(self.relay_pins, False)
        logger.info("All pins turned OFF")

    def is_active_time(self):
        """Check if current time is within active hours (5pm-11:59pm MST)."""
        now = datetime.now(self.timezone)
        current_hour = now.hour
        current_minute = now.minute

        # Check if we're between 5pm (17:00) and 11:59pm (23:59)
        if current_hour < self.start_hour:
            return False
        if current_hour > self.end_hour:
            return False
        if current_hour == self.end_hour and current_minute > self.end_minute:
            return False

        return True

    def wait_for_active_time(self):
        """Wait until the active time period begins."""
        while not self.is_active_time():
            now = datetime.now(self.timezone)
            logger.info(f"Outside active hours (5pm-11:59pm MST). Current time: {now.strftime('%I:%M %p')}. Sleeping...")
            time.sleep(60)  # Check every minute

    def sequence_random_groups(self):
        """
        Sequence 1: Randomly flicker lights by groups.
        Groups: [18, 19], [20, 21], [22, 23, 24]
        Always keeps one pin from each group active, switching every 2 seconds.
        Runs for exactly 7 iterations.
        """
        logger.info("=== STARTING SEQUENCE 1: Random Group Flicker ===")
        logger.info("Will run 7 iterations (7 different pin combinations)")

        # Initial random selection from each group
        current_pins = [random.choice(group) for group in self.groups]
        logger.info(f"Iteration 1/7: Pins selected: {current_pins}")

        # Turn on initial pins
        self.set_multiple_pins(current_pins, True)
        time.sleep(2)  # Keep pins on for 2 seconds

        # Do 6 more iterations (we already did the first one)
        for iteration in range(2, 8):
            # Select new random pins from each group
            new_pins = [random.choice(group) for group in self.groups]
            logger.info(f"Iteration {iteration}/7: Switching from {current_pins} to {new_pins}")

            # Turn off old pins and turn on new pins simultaneously
            self.set_multiple_pins(current_pins, False)
            self.set_multiple_pins(new_pins, True)

            current_pins = new_pins
            time.sleep(2)  # Keep pins on for 2 seconds

        # Clean up - turn off current pins
        self.set_multiple_pins(current_pins, False)
        logger.info("=== SEQUENCE 1 COMPLETE ===")

    def sequence_wave(self):
        """
        Sequence 2: Wave pattern.
        Turn on each pin sequentially (0.25s gaps), keep all on,
        then flash all 3 times (2s on, 1s off).
        """
        logger.info("=== STARTING SEQUENCE 2: Wave Pattern ===")

        # Phase 1: Turn on pins one by one
        logger.info("Phase 1: Building wave")
        active_pins = []
        for pin in self.relay_pins:
            self.set_pin(pin, True)
            active_pins.append(pin)
            logger.info(f"Wave building: {active_pins} ON")
            time.sleep(0.25)

        # All pins are now on
        logger.info("All pins ON - wave complete")

        # Phase 2: Flash all pins 3 times
        logger.info("Phase 2: Flashing sequence (3 times)")
        for flash_num in range(1, 4):
            logger.info(f"Flash {flash_num}/3: ON for 2 seconds")
            time.sleep(2)  # Stay on for 2 seconds

            self.all_pins_off()
            logger.info(f"Flash {flash_num}/3: OFF for 1 second")
            time.sleep(1)  # Off for 1 second

            if flash_num < 3:  # Don't turn back on after the last flash
                self.set_multiple_pins(self.relay_pins, True)

        logger.info("=== SEQUENCE 2 COMPLETE ===")

    def sequence_alternating_groups(self):
        """
        Sequence 3: Alternating groups.
        Pins [18,19,20,21] ON while [22,23,24] OFF for 2 seconds,
        then switch. Repeat 5 times.
        """
        logger.info("=== STARTING SEQUENCE 3: Alternating Groups ===")

        group_a = [18, 19, 20, 21]
        group_b = [22, 23, 24]

        for iteration in range(1, 6):
            logger.info(f"Iteration {iteration}/5: Group A {group_a} ON, Group B {group_b} OFF")
            self.set_multiple_pins(group_a, True)
            self.set_multiple_pins(group_b, False)
            time.sleep(2)

            logger.info(f"Iteration {iteration}/5: Group A {group_a} OFF, Group B {group_b} ON")
            self.set_multiple_pins(group_a, False)
            self.set_multiple_pins(group_b, True)
            time.sleep(2)

        # Turn off all pins at the end
        self.all_pins_off()
        logger.info("=== SEQUENCE 3 COMPLETE ===")

    def run_random_sequence(self):
        """Randomly select and run one of the three sequences."""
        sequences = [
            self.sequence_random_groups,
            self.sequence_wave,
            self.sequence_alternating_groups
        ]

        selected_sequence = random.choice(sequences)
        sequence_name = selected_sequence.__name__
        logger.info(f">>> Randomly selected: {sequence_name} <<<")

        selected_sequence()

    def run(self):
        """Main event loop."""
        self.running = True
        logger.info("Christmas Lights Controller started (TEST MODE)")
        logger.info(f"Active hours: 5:00 PM - 11:59 PM MST")
        logger.info("Press Ctrl+C to stop")

        try:
            while self.running:
                # Check if we're in active time
                if not self.is_active_time():
                    self.all_pins_off()
                    logger.info("NOTE: For testing, we'll skip the wait and run sequences anyway")
                    logger.info("(In production, it would wait until 5pm MST)")
                    # self.wait_for_active_time()
                    # logger.info("Entering active hours - starting sequences")

                # Run a random sequence
                self.run_random_sequence()

        except KeyboardInterrupt:
            logger.info("\nShutdown requested by user...")

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        self.running = False
        logger.info("Cleaning up...")

        # Turn off all relays
        self.all_pins_off()

        # Cleanup GPIO
        GPIO.cleanup()
        logger.info("GPIO cleanup complete. Goodbye!")

def main():
    """Main entry point."""
    try:
        controller = ChristmasLightsController()
        controller.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        GPIO.cleanup()

if __name__ == "__main__":
    main()
