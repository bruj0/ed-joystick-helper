#!/usr/bin/env python3
"""
Elite Dangerous Joystick Helper - Maps joystick button presses to keyboard sequences
"""

import time
import threading
import pygame
import logging
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
        self.config_file_path = None  # Store config file path for reloading

        # Set up logging
        self.logger = logging.getLogger("ED_Joystick_Helper")
        if not self.logger.handlers:
            # Only configure if not already configured
            handler = logging.FileHandler("ed_joystick_helper.log")
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)

        # Initialize pygame for joystick support
        pygame.init()
        pygame.joystick.init()

        # Enable keyboard events explicitly
        pygame.event.set_allowed([pygame.KEYDOWN, pygame.KEYUP])

        # Get the number of joysticks
        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            self.logger.warning("No joysticks found!")
            return

        # Initialize all joysticks
        self.joysticks = []
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            self.joysticks.append(joystick)
            self.logger.info(f"Initialized {joystick.get_name()}")
            # Initialize hat positions to centered
            for hat_id in range(joystick.get_numhats()):
                self.current_hat_positions[f"HAT_{hat_id}"] = "centered"

    def _execute_sequence(self, button_name, button_config):
        """Execute a sequence of keypresses for a button"""
        self.logger.info(f"Executing sequence for {button_name}")

        # Call preRun function if defined
        if "preRun" in button_config and callable(button_config["preRun"]):
            button_config["preRun"](button_name)

        sequence = button_config["sequence"]
        delay = button_config.get("delay", 0.1)

        for item in sequence:
            key = item["key"]
            presses = item["presses"]

            if key == "WAIT":
                # Special case for wait command
                time.sleep(presses)
                continue

            # Map key string to actual key
            key_obj = self._map_key(key)

            # Press the key the specified number of times
            for _ in range(presses):
                self.logger.debug(f"Pressing {key_obj} ({_ + 1}/{presses})")
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

    def _process_button_press(self, button_name, joy_id=None):
        """Process a button press, checking modifiers and executing sequences. Supports multiple joysticks with same button name."""
        # If joy_id is provided, use extended button name
        config_key = button_name
        if joy_id is not None:
            config_key = f"{button_name}_JOY{joy_id}"
        self.logger.debug(f"Button pressed: {config_key}")
        if config_key in self.config:
            button_config = self.config[config_key]

            # Check if this button requires a modifier
            if "modifier" in button_config:
                modifier = button_config["modifier"]
                if modifier not in self.pressed_buttons:
                    return

            # Execute the sequence in a separate thread to not block the event loop
            threading.Thread(
                target=self._execute_sequence, args=(config_key, button_config)
            ).start()

    def _process_hat_event(self, hat_id, x_value, y_value, joy_id=None):
        """Process a HAT event, converting it to a direction and triggering actions. Supports multiple joysticks."""
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
        if joy_id is not None:
            hat_name = f"{hat_name}_JOY{joy_id}"

        # Only process if the direction has changed
        if self.current_hat_positions.get(hat_name, None) != direction:
            self.current_hat_positions[hat_name] = direction

            # Create a hat event identifier that includes the direction
            hat_event = f"{hat_name}_{direction}"

            # Process the hat event if it's in the config
            self._process_button_press(hat_event)

    def set_config_file_path(self, file_path):
        """Store the config file path for reloading"""
        self.config_file_path = file_path

    def reload_config(self):
        """Reload configuration from the stored file path"""
        if not self.config_file_path:
            self.logger.error("No configuration file path set, cannot reload.")
            return False

        try:
            # Import here to avoid circular imports
            from main import load_config_from_ini

            new_config = load_config_from_ini(self.config_file_path)
            self.config = new_config
            self.logger.info(f"Configuration reloaded from {self.config_file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error reloading configuration: {e}")
            return False

    def start(self):
        """Start listening for joystick events"""
        self.running = True
        self.logger.info("Starting Elite Dangerous Joystick Helper...")

        try:
            # Main event loop
            while self.running:
                for event in pygame.event.get():
                    # self.logger.debug(f"Event: {event}")
                    if event.type == pygame.JOYBUTTONDOWN:
                        button_name = f"BUTTON_{event.button}"
                        joy_id = event.joy if hasattr(event, 'joy') else 0
                        self.pressed_buttons.add(f"{button_name}_JOY{joy_id}")
                        self._process_button_press(button_name, joy_id)
                    elif event.type == pygame.JOYBUTTONUP:
                        button_name = f"BUTTON_{event.button}"
                        joy_id = event.joy if hasattr(event, 'joy') else 0
                        pressed_name = f"{button_name}_JOY{joy_id}"
                        if pressed_name in self.pressed_buttons:
                            self.pressed_buttons.remove(pressed_name)
                    elif event.type == pygame.JOYHATMOTION:
                        hat_id = event.hat
                        x_value, y_value = event.value
                        joy_id = event.joy if hasattr(event, 'joy') else 0
                        self._process_hat_event(hat_id, x_value, y_value, joy_id)
                    elif event.type == pygame.KEYDOWN:
                        key_name = pygame.key.name(event.key)
                        key_id = (
                            f"KEY_{key_name.upper()}" if len(key_name) > 1 else key_name
                        )
                        self.logger.info(f"Key pressed: {key_id}")
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
            self.logger.info("Stopping Elite Dangerous Joystick Helper...")
        finally:
            pygame.quit()

    def stop(self):
        """Stop listening for joystick events"""
        self.running = False


def print_joystick_events():
    """Print information about connected joysticks and monitor joystick button presses"""
    # Set up logging
    logger = logging.getLogger("ED_Joystick_Helper")
    if not logger.handlers:
        logging.basicConfig(
            filename="ed_joystick_helper.log",
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    pygame.init()
    pygame.joystick.init()

    # Enable joystick events
    pygame.event.set_allowed(
        [pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYHATMOTION]
    )

    # Get the number of joysticks
    joystick_count = pygame.joystick.get_count()
    if joystick_count == 0:
        logger.warning("No joysticks found!")
        return

    # Initialize all joysticks
    joysticks = []
    for i in range(joystick_count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        joysticks.append(joystick)
        logger.info(f"Found {joystick.get_name()}")
        logger.info(f"Number of buttons: {joystick.get_numbuttons()}")
        logger.info(f"Number of axes: {joystick.get_numaxes()}")
        logger.info(f"Number of hats: {joystick.get_numhats()}")

    logger.info("Listening for joystick button presses...")

    try:
        # Main event loop
        while True:
            for event in pygame.event.get():
                # logger.debug(f"Event: {event}")  # Uncomment to see all events for debugging
                if event.type == pygame.JOYBUTTONDOWN:
                    button_name = f"BUTTON_{event.button}"
                    joy_id = event.joy if hasattr(event, 'joy') else 0
                    logger.info(f"Button pressed: {button_name}_JOY{joy_id}")
                elif event.type == pygame.JOYHATMOTION:
                    hat_id = event.hat
                    x_value, y_value = event.value
                    joy_id = event.joy if hasattr(event, 'joy') else 0
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

                    hat_name = f"HAT_{hat_id}_JOY{joy_id}"
                    logger.info(
                        f"Hat moved: {hat_name}, "
                        f"Position: {direction} ({x_value}, {y_value})"
                    )

            time.sleep(0.01)  # Small sleep to prevent CPU spinning
    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        pygame.quit()


def print_keyboard_events():
    """Monitor and print information about keyboard events for configuration"""
    # Set up logging
    logger = logging.getLogger("ED_Joystick_Helper")
    if not logger.handlers:
        logging.basicConfig(
            filename="ed_joystick_helper.log",
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    pygame.init()
    pygame.joystick.init()

    # Create a display window to capture keyboard events
    pygame.display.set_mode((300, 200))
    pygame.display.set_caption("Keyboard Event Monitor")

    # Enable keyboard events explicitly
    pygame.event.set_allowed([pygame.KEYDOWN, pygame.KEYUP])

    logger.info("Listening for key presses...")
    logger.info("Key names can be used in your configuration:")
    logger.info(" - Regular keys: Use the character (e.g., 'a', '1', '#')")
    logger.info(" - Special keys: Use 'KEY_' prefix (e.g., 'KEY_SPACE', 'KEY_F1')")

    try:
        # Main event loop
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    key_name = pygame.key.name(event.key)
                    if key_name == " ":
                        logger.info("Key pressed: 'SPACE' - Config as: KEY_SPACE")
                    elif len(key_name) == 1:
                        logger.info(
                            f"Key pressed: '{key_name}' - Config as: {key_name}"
                        )
                    else:
                        key_upper = key_name.upper()
                        logger.info(
                            f"Key pressed: '{key_name}' - "
                            f"Config as: KEY_{key_upper}"
                        )

                    # Check if it's a special key that maps to pynput's Key enum
                    from pynput.keyboard import Key

                    key_attr = key_name.lower()
                    if hasattr(Key, key_attr):
                        pynput_key = f"KEY_{key_upper}"
                        logger.info(
                            f"  This is a special key - "
                            f"Confirmed mapping: {pynput_key}"
                        )
                # Also handle window close event
                elif event.type == pygame.QUIT:
                    logger.info("Window closed, exiting...")
                    return

            pygame.display.flip()  # Update the display
            time.sleep(0.01)  # Small sleep to prevent CPU spinning
    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        pygame.quit()
