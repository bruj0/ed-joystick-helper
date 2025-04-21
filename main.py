#!/usr/bin/env python3
"""
Elite Dangerous Joystick Helper - Main entry point
"""

import argparse
import configparser
import os
import sys
from ed_joystick_helper import EDJoystickHelper, print_joystick_events, print_keyboard_events


def print_starting(caller):
    """Example pre-run function"""
    print(f"Sequence for {caller} started")


def print_end(caller):
    """Example after-run function"""
    print(f"Sequence for {caller} ended")


def load_config_from_ini(file_path):
    """Load configuration from an INI file"""
    config = configparser.ConfigParser()
    if not os.path.exists(file_path):
        print(f"Configuration file {file_path} not found.")
        sys.exit(1)

    config.read(file_path)
    parsed_config = {}
    for section in config.sections():
        parsed_config[section] = {}
        for key, value in config.items(section):
            if key == "sequence":
                parsed_config[section][key] = eval(value)  # Convert string to dictionary
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
    
    with open(file_path, 'w') as configfile:
        config.write(configfile)
    
    print(f"Default configuration file created at: {file_path}")
    print("You can edit this file to customize your joystick mappings.")


default_config = {
    "HAT_0_up": {
        # Combat 1SYS/1ENG/4WEP
        "sequence": {
            "v": 1,  # Reset PIPS
            "x": 2,  # 4WEP
        }
    },
    "HAT_0_down": {
        # Shields 4SYS/2ENG
        "sequence": {
            "v": 1,
            "c": 2 # 4SYS
        }
    },
    "HAT_0_left": {
        # Persuit 2ENG/4WEP
        "sequence": {
            "v": 1, 
            "z": 1,
            "x": 1 
        }
    },
    # Offense 3SYS/1ENG/3WEP
    "HAT_0_right": {
        "sequence": {
            "v": 1,
            "c": 1,  # 3SYS
            "x": 1,  # 3WEP
        }
    },
}

def main():
    """Main entry point for the application"""
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

    args = parser.parse_args()

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
                print(f"Using configuration from: {config_file}")
                helper = EDJoystickHelper(config)
            except Exception as e:
                print(f"Error loading configuration: {e}")
                print("Falling back to default configuration.")
                helper = EDJoystickHelper(default_config)
        else:
            print(f"Configuration file not found: {config_file}")
            print("Using default configuration.")
            helper = EDJoystickHelper(default_config)
        
        helper.start()


if __name__ == "__main__":
    main()
