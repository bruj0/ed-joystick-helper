#!/usr/bin/env python3
"""
Elite Dangerous Joystick Helper - Maps joystick button presses to keyboard sequences
"""

import time
import threading
import pygame
from pynput.keyboard import Key, Controller


class EDJoystickHelper:
    def __init__(self, config):
        """
        Initialize the helper with a configuration dictionary

        Args:
            config: Dictionary mapping buttons to sequences of keypresses
        """
        self.config = config
        self.keyboard = Controller()
        self.running = False
        self.pressed_buttons = set()
        self.current_hat_positions = {}  # Track current hat positions

        # Initialize pygame for joystick support
        pygame.init()
        pygame.joystick.init()

        # Enable keyboard events explicitly
        pygame.event.set_allowed([pygame.KEYDOWN, pygame.KEYUP])

        # Get the number of joysticks
        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            print("No joysticks found!")
            return

        # Initialize all joysticks
        self.joysticks = []
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            self.joysticks.append(joystick)
            print(f"Initialized {joystick.get_name()}")
            # Initialize hat positions to centered
            for hat_id in range(joystick.get_numhats()):
                self.current_hat_positions[f"HAT_{hat_id}"] = "centered"

    def _execute_sequence(self, button_name, button_config):
        """Execute a sequence of keypresses for a button"""
        print(f"Executing sequence for {button_name}")

        # Call preRun function if defined
        if "preRun" in button_config and callable(button_config["preRun"]):
            button_config["preRun"](button_name)

        sequence = button_config["sequence"]
        delay = button_config.get("delay", 0.1)

        for key, presses in sequence.items():
            if key == "WAIT":
                # Special case for wait command
                time.sleep(presses)
                continue

            # Map key string to actual key
            key_obj = self._map_key(key)

            # Press the key the specified number of times
            for _ in range(presses):
                print(f"Pressing {key_obj} ({_ + 1}/{presses})")
                self.keyboard.press(key_obj)
                time.sleep(delay)
                self.keyboard.release(key_obj)
                time.sleep(delay)

        # Call afterRun function if defined
        if "afterRun" in button_config and callable(button_config["afterRun"]):
            button_config["afterRun"](button_name)

    def _map_key(self, key_name):
        """Map a key name string to a pynput key object"""
        # Check if it's a special key
        if key_name.startswith("KEY_"):
            key_attr = key_name[4:].lower()
            if hasattr(Key, key_attr):
                return getattr(Key, key_attr)

        # Otherwise, assume it's a character
        return key_name

    def _process_button_press(self, button_name):
        """Process a button press, checking modifiers and executing sequences"""
        print(f"Button pressed: {button_name}")
        if button_name in self.config:
            button_config = self.config[button_name]

            # Check if this button requires a modifier
            if "modifier" in button_config:
                modifier = button_config["modifier"]
                if modifier not in self.pressed_buttons:
                    return

            # Execute the sequence in a separate thread to not block the event loop
            threading.Thread(
                target=self._execute_sequence, args=(button_name, button_config)
            ).start()

    def _process_hat_event(self, hat_id, x_value, y_value):
        """Process a HAT event, converting it to a direction and triggering actions"""
        # Map hat position to direction
        direction = "centered"
        if x_value == 0 and y_value == 1:
            direction = "up"
        elif x_value == 1 and y_value == 1:
            direction = "up-right"
        elif x_value == 1 and y_value == 0:
            direction = "right"
        elif x_value == 1 and y_value == -1:
            direction = "down-right"
        elif x_value == 0 and y_value == -1:
            direction = "down"
        elif x_value == -1 and y_value == -1:
            direction = "down-left"
        elif x_value == -1 and y_value == 0:
            direction = "left"
        elif x_value == -1 and y_value == 1:
            direction = "up-left"

        hat_name = f"HAT_{hat_id}"

        # Only process if the direction has changed
        if self.current_hat_positions[hat_name] != direction:
            self.current_hat_positions[hat_name] = direction

            # Create a hat event identifier that includes the direction
            hat_event = f"{hat_name}_{direction}"

            # Process the hat event if it's in the config
            self._process_button_press(hat_event)

    def start(self):
        """Start listening for joystick events"""
        self.running = True
        print("Starting Elite Dangerous Joystick Helper...")
        print("Press Ctrl+C to quit")

        try:
            # Main event loop
            while self.running:
                for event in pygame.event.get():
                    # print(f"Event: {event}")
                    if event.type == pygame.JOYBUTTONDOWN:
                        button_name = f"BUTTON_{event.button}"
                        self.pressed_buttons.add(button_name)
                        self._process_button_press(button_name)
                    elif event.type == pygame.JOYBUTTONUP:
                        button_name = f"BUTTON_{event.button}"
                        if button_name in self.pressed_buttons:
                            self.pressed_buttons.remove(button_name)
                    elif event.type == pygame.JOYHATMOTION:
                        hat_id = event.hat
                        x_value, y_value = event.value
                        self._process_hat_event(hat_id, x_value, y_value)
                    elif event.type == pygame.KEYDOWN:
                        key_name = pygame.key.name(event.key)
                        key_id = (
                            f"KEY_{key_name.upper()}" if len(key_name) > 1 else key_name
                        )
                        print(f"Key pressed: {key_id}")
                        # Process the key press as if it were a button
                        self._process_button_press(key_id)
                    elif event.type == pygame.KEYUP:
                        key_name = pygame.key.name(event.key)
                        key_id = (
                            f"KEY_{key_name.upper()}" if len(key_name) > 1 else key_name
                        )
                        if key_id in self.pressed_buttons:
                            self.pressed_buttons.remove(key_id)

                time.sleep(0.01)  # Small sleep to prevent CPU spinning
        except KeyboardInterrupt:
            print("\nStopping Elite Dangerous Joystick Helper...")
        finally:
            pygame.quit()

    def stop(self):
        """Stop listening for joystick events"""
        self.running = False


def print_joystick_events():
    """Print information about connected joysticks and monitor joystick button presses"""
    pygame.init()
    pygame.joystick.init()

    # Enable joystick events
    pygame.event.set_allowed([pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYHATMOTION])

    # Get the number of joysticks
    joystick_count = pygame.joystick.get_count()
    if joystick_count == 0:
        print("No joysticks found!")
        return

    # Initialize all joysticks
    joysticks = []
    for i in range(joystick_count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        joysticks.append(joystick)
        print(f"Found {joystick.get_name()}")
        print(f"Number of buttons: {joystick.get_numbuttons()}")
        print(f"Number of axes: {joystick.get_numaxes()}")
        print(f"Number of hats: {joystick.get_numhats()}")

    print("\nListening for joystick button presses. Press Ctrl+C to quit...")

    try:
        # Main event loop
        while True:
            for event in pygame.event.get():
                print(f"Event: {event}")  # Uncomment to see all events for debugging
                if event.type == pygame.JOYBUTTONDOWN:
                    button_name = f"BUTTON_{event.button}"
                    print(f"Button pressed: {button_name}")
                elif event.type == pygame.JOYHATMOTION:
                    hat_id = event.hat
                    x_value, y_value = event.value
                    direction = "centered"

                    # Map hat position to direction
                    if x_value == 0 and y_value == 1:
                        direction = "up"
                    elif x_value == 1 and y_value == 1:
                        direction = "up-right"
                    elif x_value == 1 and y_value == 0:
                        direction = "right"
                    elif x_value == 1 and y_value == -1:
                        direction = "down-right"
                    elif x_value == 0 and y_value == -1:
                        direction = "down"
                    elif x_value == -1 and y_value == -1:
                        direction = "down-left"
                    elif x_value == -1 and y_value == 0:
                        direction = "left"
                    elif x_value == -1 and y_value == 1:
                        direction = "up-left"

                    hat_name = f"HAT_{hat_id}"
                    print(
                        f"Hat moved: {hat_name}, "
                        f"Position: {direction} ({x_value}, {y_value})"
                    )

            time.sleep(0.01)  # Small sleep to prevent CPU spinning
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        pygame.quit()


def print_keyboard_events():
    """Monitor and print information about keyboard events for configuration"""
    pygame.init()
    pygame.joystick.init()

    # Create a display window to capture keyboard events
    pygame.display.set_mode((300, 200))
    pygame.display.set_caption("Keyboard Event Monitor")

    # Enable keyboard events explicitly
    pygame.event.set_allowed([pygame.KEYDOWN, pygame.KEYUP])

    print("\nListening for key presses. Press Ctrl+C to quit...")
    print("Key names can be used in your configuration:")
    print(" - Regular keys: Use the character (e.g., 'a', '1', '#')")
    print(" - Special keys: Use 'KEY_' prefix (e.g., 'KEY_SPACE', 'KEY_F1')")

    try:
        # Main event loop
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    key_name = pygame.key.name(event.key)
                    if key_name == " ":
                        print("Key pressed: 'SPACE' - Config as: KEY_SPACE")
                    elif len(key_name) == 1:
                        print(f"Key pressed: '{key_name}' - Config as: {key_name}")
                    else:
                        key_upper = key_name.upper()
                        print(
                            f"Key pressed: '{key_name}' - "
                            f"Config as: KEY_{key_upper}"
                        )

                    # Check if it's a special key that maps to pynput's Key enum
                    from pynput.keyboard import Key

                    key_attr = key_name.lower()
                    if hasattr(Key, key_attr):
                        pynput_key = f"KEY_{key_upper}"
                        print(
                            f"  This is a special key - "
                            f"Confirmed mapping: {pynput_key}"
                        )
                # Also handle window close event
                elif event.type == pygame.QUIT:
                    print("\nWindow closed, exiting...")
                    return

            pygame.display.flip()  # Update the display
            time.sleep(0.01)  # Small sleep to prevent CPU spinning
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        pygame.quit()
