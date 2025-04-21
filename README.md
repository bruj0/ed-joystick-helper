# Elite Dangerous Joystick to Keyboard Helper

A Python application that maps joystick button presses and hat movements to keyboard sequences, specifically designed to help Elite Dangerous players automate common actions like power distribution management.

## Disclaimer 

This utility can be considered a breach of TOS for some games, please make sure you understand the consequences.

## Features

- Maps joystick buttons and hat directions to keyboard sequences
- Supports modifier buttons (combinations)
- Configurable delays between key presses
- Supports special wait commands in sequences
- Can execute pre-run and post-run functions
- Includes a helper to identify joystick buttons and keyboard keys
- Configuration via INI file or Python dictionary
- Runs in the system tray with options to reload configuration and exit
- 
### Power Configuration Presets (PIPS)

The default configuration is set up for Elite Dangerous

* Combat 1SYS/1ENG/4WEP
* Shields 4SYS/2ENG
* Persuit 2ENG/4WEP
* Offense 3SYS/1ENG/3WEP

## Command-Line Options

The application supports several command-line options:

```
-h, --help                       Show the help message and exit
--joystick-events                Monitor and display joystick button events
--keyboard-events                Monitor and display keyboard events
--config FILE                    Specify a custom configuration file path
--create-config                  Create a default configuration file
--no-tray                        Run in console mode without system tray icon
--console                        Run in console mode (not in background)
--background                     Detach the application to run in the background (Windows only)
```

### Running in the Background

To run the application fully detached from the console (in the background) on Windows, use:

```bash
python main.py --background
```

This will start the tray application and immediately return you to the command prompt. The application will continue running in the background with a system tray icon.

Note: The `--background` option is only supported on Windows.

## System Tray Features

By default, the application now runs in the background with a system tray icon. This provides:

- Minimal footprint: The application runs silently in the background
- Easy access: Right-click on the system tray icon to access options
- Reload configuration: Update your settings without restarting the application
- Clean exit: Properly shutdown the application when you're done

To disable the system tray and run in the traditional console mode, use the `--no-tray` option:

## Installation

### Direct Download

You can download the latest pre-built Windows executable from the [GitHub Releases page](https://github.com/bruj0/ed-joystick-helper/releases). 
Simply download the ZIP file, extract it, and run the executable.
You can see how it was created in the [Action tab](https://github.com/bruj0/ed-joystick-helper/actions/runs/14579316113/job/40892291548)

### Prerequisites for running with Python executable

- Python 3.6+
- Windows operating system
- A joystick or controller
- Elite Dangerous game (optional, but that's what it's designed for)

### Setup

1. Clone this repository or download the source code
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or:

```bash
pip install pygame pynput
```

## Usage

### Basic Usage

Run the application with default configuration:

```bash
python main.py
```

This will use the `config.ini` file in the same directory, or fall back to the built-in default configuration if the file doesn't exist.

### Creating a Default Configuration File

```bash
python main.py --create-config
```

This will create a `config.ini` file with the default PIPS (Power Distribution) presets.

### Identifying Joystick Buttons

To see which buttons on your controller correspond to which button IDs:

```bash
python main.py --joystick-events
```

Press buttons on your joystick or move the hat to see the output. Use these names in your configuration.

### Identifying Keyboard Keys

To see how keyboard keys are identified:

```bash
python main.py --keyboard-events
```

Press keys on your keyboard to see their names. Use these names in your configuration.

## Configuration

You can configure the application using an INI file. Here's an example of the default configuration for Elite Dangerous power management:

```ini
[HAT_0_up]
sequence = [{"key": "v", "presses": 1}, {"key": "x", "presses": 2}]

[HAT_0_down]
sequence = [{"key": "v", "presses": 1}, {"key": "c", "presses": 2}]

[HAT_0_left]
sequence = [{"key": "v", "presses": 1}, {"key": "z", "presses": 1}, {"key": "x", "presses": 1}]

[HAT_0_right]
sequence = [{"key": "v", "presses": 1}, {"key": "c", "presses": 1}, {"key": "x", "presses": 1}]
```

### Power Configuration Presets (PIPS)

The default configuration is set up for Elite Dangerous power distribution using the hat switch:

- **HAT_0_up**: Combat (4-2-0) - 4 pips to Weapons, 2 to Engines, 0 to Systems
  - Presses 'v' once (reset PIPS) and 'x' twice (add to Weapons)
  
- **HAT_0_down**: Defensive (4-2-0) - 4 pips to Systems, 2 to Engines, 0 to Weapons
  - Presses 'v' once (reset PIPS) and 'c' twice (add to Systems)
  
- **HAT_0_left**: Pursuit (0-2-4) - 0 to Systems, 2 to Engines, 4 to Weapons
  - Presses 'v' once (reset PIPS), 'z' once (add to Engines), and 'x' once (add to Weapons)
  
- **HAT_0_right**: Balanced (2-1-3) - 2 to Systems, 1 to Engines, 3 to Weapons
  - Presses 'v' once (reset PIPS), 'c' once (add to Systems), and 'x' once (add to Weapons)

### Advanced Configuration

For advanced configuration, you can modify the code directly to include modifiers and functions. Here's an example from the description:

```python
config = {
    'BUTTON_29': {
        'modifier': 'BUTTON_23',  # Only triggered if both buttons are pressed
        'delay': 0.5,  # delay between key presses
        'sequence': [
            {"key": "KEY_UP", "presses": 3},  # Press Up Arrow 3 times
            {"key": "KEY_DOWN", "presses": 1},  # Press Down Arrow 1 time
            {"key": "WAIT", "presses": 1.5},  # Wait 1.5 seconds
        ],
        'preRun': print_starting,  # Function to call before sequence
        'afterRun': print_end,  # Function to call after sequence
    }
}
```

## Default Elite Dangerous Key Bindings

The default configuration assumes the following Elite Dangerous key bindings:

- `v`: Reset Power Distribution
- `z`: Increase Power to Engines
- `x`: Increase Power to Weapons
- `c`: Increase Power to Systems

You may need to adjust your key bindings in Elite Dangerous or modify the configuration to match your setup.

## Troubleshooting

- **No joystick found**: Ensure your joystick is connected and recognized by Windows.
- **Key presses not working**: Make sure Elite Dangerous is in focus when using the app.
- **Configuration file errors**: Check your configuration syntax; you may need to recreate the config file.

## License

This project is open source and available under the MIT License.