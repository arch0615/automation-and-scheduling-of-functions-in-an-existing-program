"""
GUI Automation Engine
Controls Housoft applications by simulating human mouse/keyboard input.
Uses OpenCV for image recognition to find UI elements.
"""

import time
import random
import logging
import pyautogui
import cv2
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

# Safety: prevent pyautogui from moving too fast
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort


class GUIEngine:
    """Controls Housoft windows via GUI automation."""

    TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

    def __init__(self):
        self.current_app = None  # 'face' or 'insta'
        self.current_module = None
        self.is_task_running = False
        logger.info("GUIEngine initialized")

    # ─── Window Management ───────────────────────────────────

    def find_window(self, app_name):
        """Find Housoft window by app name ('face' or 'insta')."""
        try:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
            windows = desktop.windows()

            search_term = "Housoft Face" if app_name == "face" else "Housoft Insta"

            for win in windows:
                if search_term.lower() in win.window_text().lower():
                    logger.info(f"Found window: {win.window_text()}")
                    return win

            logger.warning(f"Window not found for: {search_term}")
            return None
        except Exception as e:
            logger.error(f"Error finding window: {e}")
            return None

    def bring_to_front(self, app_name):
        """Bring the specified Housoft app to foreground."""
        window = self.find_window(app_name)
        if window:
            try:
                window.set_focus()
                time.sleep(0.5)
                self.current_app = app_name
                logger.info(f"Brought {app_name} to front")
                return True
            except Exception as e:
                logger.error(f"Error bringing window to front: {e}")
        return False

    # ─── Image Recognition ───────────────────────────────────

    def take_screenshot(self):
        """Take a screenshot and return as numpy array for OpenCV."""
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def find_element(self, template_name, confidence=0.8):
        """
        Find a UI element on screen using template matching.
        Returns (x, y) center coordinates or None if not found.
        """
        template_path = self.TEMPLATES_DIR / f"{template_name}.png"
        if not template_path.exists():
            logger.error(f"Template not found: {template_path}")
            return None

        screenshot = self.take_screenshot()
        template = cv2.imread(str(template_path))

        if template is None:
            logger.error(f"Could not load template: {template_path}")
            return None

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            logger.info(f"Found '{template_name}' at ({center_x}, {center_y}) confidence={max_val:.2f}")
            return (center_x, center_y)

        logger.warning(f"Element '{template_name}' not found (best confidence={max_val:.2f})")
        return None

    # ─── Click Actions ───────────────────────────────────────

    def click_element(self, template_name, confidence=0.8, retries=3):
        """Find and click a UI element. Retries if not found."""
        for attempt in range(retries):
            pos = self.find_element(template_name, confidence)
            if pos:
                # Add small random offset to simulate human behavior
                offset_x = random.randint(-3, 3)
                offset_y = random.randint(-3, 3)
                pyautogui.click(pos[0] + offset_x, pos[1] + offset_y)
                logger.info(f"Clicked '{template_name}' at ({pos[0]}, {pos[1]})")
                time.sleep(random.uniform(0.3, 0.8))
                return True

            if attempt < retries - 1:
                logger.info(f"Retry {attempt + 1}/{retries} for '{template_name}'")
                time.sleep(1)

        logger.error(f"Failed to click '{template_name}' after {retries} attempts")
        return False

    def click_position(self, x, y):
        """Click at specific coordinates with human-like randomness."""
        offset_x = random.randint(-2, 2)
        offset_y = random.randint(-2, 2)
        pyautogui.click(x + offset_x, y + offset_y)
        time.sleep(random.uniform(0.3, 0.7))

    # ─── Task Control ────────────────────────────────────────

    def execute_sequence(self, sequence, context=None):
        """
        Execute a click sequence (list of step dicts).
        Each step: type, template/x,y, seconds, label, etc.
        """
        context = context or {}
        for i, step in enumerate(sequence):
            step_type = step.get("type")
            label = step.get("label", f"Step {i+1}")
            logger.info(f"  [{i+1}/{len(sequence)}] {label}")

            if step_type == "click":
                if not self.click_element(step["template"]):
                    logger.error(f"Step failed: {label}")
                    return False

            elif step_type == "click_xy":
                self.click_position(step["x"], step["y"])

            elif step_type == "wait":
                seconds = step.get("seconds", 1.0)
                # Add small random variation
                seconds *= random.uniform(0.9, 1.2)
                time.sleep(seconds)

            elif step_type == "verify":
                if not self.find_element(step["template"]):
                    logger.error(f"Verify failed: {step['template']} not found")
                    return False

            else:
                logger.warning(f"Unknown step type: {step_type}")

        return True

    def start_task(self, app_name, module_name):
        """Start a specific task in Housoft using its defined click sequence."""
        from core.click_sequences import get_start_sequence

        logger.info(f"Starting task: {app_name} -> {module_name}")

        # Step 1: Bring correct app to front
        if not self.bring_to_front(app_name):
            logger.error(f"Cannot bring {app_name} to front")
            return False

        time.sleep(random.uniform(0.5, 1.0))

        # Step 2: Execute the module's start sequence
        sequence = get_start_sequence(module_name)
        if not sequence:
            logger.error(f"No start sequence defined for: {module_name}")
            return False

        if not self.execute_sequence(sequence):
            logger.error(f"Start sequence failed for: {module_name}")
            return False

        self.current_module = module_name
        self.is_task_running = True
        logger.info(f"Task started: {app_name} -> {module_name}")
        return True

    def stop_task(self):
        """Stop the currently running task using the stop sequence."""
        from core.click_sequences import get_stop_sequence

        logger.info("Stopping current task...")

        if not self.is_task_running:
            logger.info("No task is running")
            return True

        sequence = get_stop_sequence(self.current_module)
        if self.execute_sequence(sequence):
            self.is_task_running = False
            logger.info(f"Task stopped: {self.current_module}")
            self.current_module = None
            return True

        logger.error("Failed to stop task")
        return False

    def switch_task(self, app_name, module_name):
        """Stop current task and start a new one."""
        logger.info(f"Switching to: {app_name} -> {module_name}")

        # Stop current task if running
        if self.is_task_running:
            if not self.stop_task():
                logger.error("Failed to stop current task before switching")
                return False
            time.sleep(random.uniform(2.0, 4.0))

        # Start new task
        return self.start_task(app_name, module_name)

    # ─── State Detection ─────────────────────────────────────

    def detect_popup(self):
        """Check if an unexpected popup/dialog is on screen."""
        popup_templates = ["popup_error", "popup_blocked", "popup_alert"]
        for template in popup_templates:
            if self.find_element(template, confidence=0.7):
                logger.warning(f"Popup detected: {template}")
                return template
        return None

    def dismiss_popup(self):
        """Try to dismiss any popup by clicking OK or X."""
        popup = self.detect_popup()
        if popup:
            if self.click_element("popup_ok_btn", confidence=0.7):
                logger.info("Popup dismissed via OK button")
                return True
            if self.click_element("popup_close_btn", confidence=0.7):
                logger.info("Popup dismissed via close button")
                return True
        return False

    def check_task_status(self):
        """Check if a task is still running by looking for indicators."""
        if self.find_element("status_running", confidence=0.7):
            return "running"
        if self.find_element("status_stopped", confidence=0.7):
            return "stopped"
        if self.find_element("status_error", confidence=0.7):
            return "error"
        return "unknown"

    # ─── Utility ─────────────────────────────────────────────

    def human_delay(self, min_sec=1.0, max_sec=3.0):
        """Wait a random amount of time to simulate human behavior."""
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"Human delay: {delay:.1f}s")
        time.sleep(delay)

    def capture_template(self, name, region=None):
        """Capture a screenshot (or region) and save as template for future matching."""
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()

        save_path = self.TEMPLATES_DIR / f"{name}.png"
        screenshot.save(str(save_path))
        logger.info(f"Template saved: {save_path}")
        return save_path
