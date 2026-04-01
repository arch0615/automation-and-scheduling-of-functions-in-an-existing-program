"""
Window Manager
Handles finding, focusing, and managing Housoft application windows.
"""

import time
import logging

logger = logging.getLogger(__name__)


class WindowManager:
    """Manages Housoft Face and Housoft Insta windows."""

    WINDOW_TITLES = {
        "face": "Housoft Face",
        "insta": "Housoft Insta",
    }

    def __init__(self):
        self._windows = {}
        logger.info("WindowManager initialized")

    def refresh_windows(self):
        """Scan for all Housoft windows."""
        try:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
            all_windows = desktop.windows()

            self._windows = {}
            for win in all_windows:
                title = win.window_text().lower()
                for app_key, search_title in self.WINDOW_TITLES.items():
                    if search_title.lower() in title:
                        self._windows[app_key] = win
                        logger.info(f"Found {app_key} window: {win.window_text()}")

            return self._windows
        except Exception as e:
            logger.error(f"Error scanning windows: {e}")
            return {}

    def get_window(self, app_name):
        """Get window handle for an app. Refreshes if not cached."""
        if app_name not in self._windows:
            self.refresh_windows()
        return self._windows.get(app_name)

    def focus_app(self, app_name):
        """Bring a Housoft app window to the foreground."""
        window = self.get_window(app_name)
        if window:
            try:
                if window.is_minimized():
                    window.restore()
                window.set_focus()
                time.sleep(0.5)
                logger.info(f"Focused: {app_name}")
                return True
            except Exception as e:
                logger.error(f"Error focusing {app_name}: {e}")
                # Window reference may be stale, clear cache
                self._windows.pop(app_name, None)
        else:
            logger.warning(f"Window not found for {app_name}")
        return False

    def is_app_running(self, app_name):
        """Check if a Housoft app is currently running."""
        self.refresh_windows()
        return app_name in self._windows

    def get_window_rect(self, app_name):
        """Get the position and size of a Housoft window."""
        window = self.get_window(app_name)
        if window:
            try:
                rect = window.rectangle()
                return {
                    "left": rect.left,
                    "top": rect.top,
                    "width": rect.width(),
                    "height": rect.height(),
                }
            except Exception as e:
                logger.error(f"Error getting window rect: {e}")
        return None

    def list_running_apps(self):
        """Return list of currently running Housoft apps."""
        self.refresh_windows()
        return list(self._windows.keys())
