#!/usr/bin/env python3
"""
Elite Dangerous Joystick Helper - System Tray Icon Implementation
"""

import os
import threading
import pystray
import logging
from PIL import Image, ImageDraw
from ed_joystick_helper import EDJoystickHelper


# Configure logging
def setup_logging():
    """Set up logging to file"""
    log_file = "ed_joystick_helper.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("ED_Joystick_Helper")
    return logger


# Create a simple icon for the system tray
def create_icon():
    """Create a simple icon for the system tray"""
    width = 64
    height = 64
    color1 = (0, 128, 255)  # Light blue
    color2 = (255, 128, 0)  # Orange
    image = Image.new("RGB", (width, height), color=(0, 0, 0))
    dc = ImageDraw.Draw(image)
    # Draw a simple joystick-like icon
    dc.rectangle((10, 40, 54, 54), fill=color1)  # Base
    dc.ellipse((20, 10, 44, 34), fill=color2)  # Joystick top
    return image


class EDJoystickTray:
    """Class to manage the system tray icon and application lifecycle"""

    def __init__(self, config_path, config=None):
        self.config_path = config_path
        self.config = config
        self.helper = None
        self.helper_thread = None
        self.icon = None
        self.icon_thread = None
        self.logger = setup_logging()

    def start(self):
        """Start the application with system tray icon"""
        # Start the helper in a separate thread
        self.helper = EDJoystickHelper(self.config)
        self.helper.set_config_file_path(self.config_path)

        self.helper_thread = threading.Thread(target=self.helper.start, daemon=True)
        self.helper_thread.start()

        # Create and run system tray icon
        icon_image = create_icon()
        self.icon = pystray.Icon(
            "ed_joystick_helper",
            icon=icon_image,
            title="ED Joystick Helper",
            menu=pystray.Menu(
                pystray.MenuItem("Reload Config", self.reload_config),
                pystray.MenuItem("Exit", self.exit_app),
            ),
        )

        self.logger.info("ED Joystick Helper is running in the background.")
        self.logger.info("Right-click on the system tray icon for options.")

        # Start the icon in a separate non-daemon thread
        # Using non-daemon thread ensures the app stays alive even if main thread exits
        self.icon_thread = threading.Thread(target=self.icon.run, daemon=False)
        self.icon_thread.start()

    def join(self):
        """Wait for the icon thread to complete (optional method to block if needed)"""
        if self.icon_thread and self.icon_thread.is_alive():
            self.icon_thread.join()

    def detach_to_background(self):
        """Detach the application to run in the background without blocking the main thread"""
        import time
        import threading

        self.logger.info("ED Joystick Helper detached to background")

        # Create a background thread that will keep the application alive
        # This thread is non-daemon, so it will keep the process running
        # even after the main thread exits
        def keep_alive():
            self.logger.info("Background thread started")
            # Sleep for a very short time to allow the main thread to exit
            time.sleep(0.1)
            # Now we're running in the background

            # Loop until the icon thread is no longer alive
            # This thread will exit when the icon thread exits
            while self.icon_thread and self.icon_thread.is_alive():
                time.sleep(1.0)

        # Start the keep-alive thread as non-daemon
        threading.Thread(target=keep_alive, daemon=False).start()
        return True

    def reload_config(self, icon, item):
        """Reload configuration from file"""
        success = self.helper.reload_config()
        if success:
            self.logger.info("Configuration reloaded successfully")
            icon.notify("Configuration reloaded successfully", "ED Joystick Helper")
        else:
            self.logger.error("Failed to reload configuration")
            icon.notify("Failed to reload configuration", "ED Joystick Helper")

    def exit_app(self, icon, item):
        """Exit the application"""
        self.logger.info("Shutting down ED Joystick Helper")
        icon.visible = False
        self.helper.stop()
        icon.stop()
        # Give helper thread time to clean up
        self.helper_thread.join(timeout=1.0)
        # Force exit in case threads are hanging
        os._exit(0)
