#!/usr/bin/env python3
"""
Elite Dangerous Joystick Helper - Main entry point
"""

import argparse
import configparser
import os
import sys
import logging
import subprocess
from PIL import Image, ImageDraw
from ed_joystick_helper import (
    EDJoystickHelper,
    print_joystick_events,
    print_keyboard_events,
)
from ed_joystick_tray import EDJoystickTray


def setup_normal_logging():
    """Set up logging to file"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("ED_Joystick_Helper")
    return logger


def print_starting(caller):
    """Example pre-run function"""
    logger = logging.getLogger("ED_Joystick_Helper")
    logger.info(f"Sequence for {caller} started")


def print_end(caller):
    """Example after-run function"""
    logger = logging.getLogger("ED_Joystick_Helper")
    logger.info(f"Sequence for {caller} ended")


def load_config_from_ini(file_path):
    """Load configuration from an INI file"""
    logger = logging.getLogger("ED_Joystick_Helper")
    config = configparser.ConfigParser()
    if not os.path.exists(file_path):
        logger.error(f"Configuration file {file_path} not found.")
        sys.exit(1)

    config.read(file_path)
    parsed_config = {}
    for section in config.sections():
        parsed_config[section] = {}
        for key, value in config.items(section):
            if key == "sequence":
                # Convert string to list of key-press objects
                try:
                    parsed_config[section][key] = eval(value)
                except (SyntaxError, NameError) as e:
                    logger.error(f"Error parsing sequence in section {section}: {e}")
                    logger.error(f"Value was: {value}")
                    # Provide a default empty sequence
                    parsed_config[section][key] = []
            elif key == "delay":
                # Convert delay to float
                parsed_config[section][key] = float(value)
            elif key == "modifier":
                # Store modifier as string
                parsed_config[section][key] = value
            else:
                # Try to convert to appropriate type if possible
                try:
                    parsed_config[section][key] = eval(value)
                except (SyntaxError, NameError):
                    parsed_config[section][key] = value

    # Add function references if defined in the default_config
    for section in parsed_config:
        if section in default_config:
            for func_key in ["preRun", "afterRun"]:
                if func_key in default_config[section]:
                    parsed_config[section][func_key] = default_config[section][func_key]

    return parsed_config


def create_default_config_file(file_path, config_dict):
    """Create a default INI configuration file"""
    logger = logging.getLogger("ED_Joystick_Helper")
    config = configparser.ConfigParser()

    for button, settings in config_dict.items():
        config[button] = {}
        for key, value in settings.items():
            if key in ("preRun", "afterRun"):
                # Skip function references as they can't be serialized directly
                continue
            if key == "delay":
                config[button][key] = str(value)
            elif key == "sequence":
                # Convert sequence dict to string representation
                config[button][key] = str(value)
            else:
                config[button][key] = str(value)

    # Make sure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w") as configfile:
        config.write(configfile)

    logger.info(f"Default configuration file created at: {file_path}")
    logger.info("You can edit this file to customize your joystick mappings.")


default_config = {
    "HAT_0_up": {
        # Combat 1SYS/1ENG/4WEP
        "sequence": [
            {"key": "v", "presses": 1},  # Reset PIPS
            {"key": "x", "presses": 2},  # 4WEP
        ]
    },
    "HAT_0_down": {
        # Shields 4SYS/2ENG
        "sequence": [
            {"key": "v", "presses": 1}, 
            {"key": "c", "presses": 2}  # 4SYS
        ]
    },
    "HAT_0_left": {
        # Persuit 2ENG/4WEP
        "sequence": [
            {"key": "v", "presses": 1}, 
            {"key": "z", "presses": 1}, 
            {"key": "x", "presses": 1}
        ]
    },
    # Offense 3SYS/1ENG/3WEP
    "HAT_0_right": {
        "sequence": [
            {"key": "v", "presses": 1},
            {"key": "c", "presses": 1},  # 3SYS
            {"key": "x", "presses": 1},  # 3WEP
        ]
    },
    "BUTTON_27": {
        "sequence": [
            {"key": "n", "presses": 1},
            {"key": "WAIT", "presses": 1},
            {"key": "e", "presses": 2},
            {"key": "KEY_SPACE", "presses": 1},
            {"key": "d", "presses": 1},
            {"key": "KEY_SPACE", "presses": 1},
            {"key": "e", "presses": 2},
            {"key": "n", "presses": 1},
        ],
    },
}


def main():
    """Main entry point for the application"""
    # Set up logging first thing

    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_config_path = os.path.join(script_dir, "config.ini")

    parser = argparse.ArgumentParser(
        description="Elite Dangerous Joystick Helper - Maps joystick buttons to keyboard sequences"
    )
    parser.add_argument(
        "--joystick-events",
        action="store_true",
        help="Print joystick information and monitor joystick button presses",
    )
    parser.add_argument(
        "--keyboard-events",
        action="store_true",
        help="Monitor keyboard events for configuration purposes",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=default_config_path,
        help=f"Path to the INI configuration file (default: {default_config_path})",
    )
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create default configuration file if it doesn't exist",
    )
    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Run the application without system tray icon (console mode)",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Run the application in console mode (not in background)",
    )
    parser.add_argument(
        "--background",
        action="store_true",
        help="Detach the application to run in the background after startup",
    )

    args = parser.parse_args()
    logger = setup_normal_logging()

    if args.joystick_events:
        print_joystick_events()
    elif args.keyboard_events:
        print_keyboard_events()
    else:
        config_file = args.config

        # Create config file if requested or if it doesn't exist and create-config flag is set
        if args.create_config and not os.path.exists(config_file):
            create_default_config_file(config_file, default_config)
            return

        # Use INI config if it exists, otherwise fall back to default
        if os.path.exists(config_file):
            try:
                config = load_config_from_ini(config_file)
                logger.info(f"Using configuration from: {config_file}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                logger.info("Falling back to default configuration.")
                config = default_config
        else:
            logger.warning(f"Configuration file not found: {config_file}")
            logger.info("Using default configuration.")
            config = default_config

        # Run with or without system tray based on command line argument
        if args.no_tray or args.console:
            # Original direct mode with console output
            logger.info("Running in console mode")
            helper = EDJoystickHelper(config)
            helper.set_config_file_path(config_file)
            helper.start()
        elif args.background:
            # Relaunch the script in a detached process and exit parent
            if os.name == 'nt':
                DETACHED_PROCESS = 0x00000008
                subprocess.Popen([
                    sys.executable, os.path.abspath(__file__),
                    *(arg for arg in sys.argv[1:] if arg != '--background')
                ], creationflags=DETACHED_PROCESS, close_fds=True)
                logger.info("Application detached to background. Exiting parent process.")
                sys.exit(0)
            else:
                logger.error("--background is only implemented for Windows.")
                sys.exit(1)
        else:
            # System tray mode (default) - runs in background
            logger.info("Starting in background mode with system tray")
            app = EDJoystickTray(config_file, config)
            try:
                app.start()
                logger.info("Application is running in the system tray")
                # Block the main thread until the icon thread completes
                # This keeps the application alive
                app.join()
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, shutting down")
                if app.icon and hasattr(app.icon, 'visible'):
                    app.exit_app(app.icon, None)


if __name__ == "__main__":
    main()
