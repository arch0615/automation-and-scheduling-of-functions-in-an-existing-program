"""
Mock GUI Engine for end-to-end testing without live Housoft.
Implements the same interface as GUIEngine but simulates all actions with logs.
Used for testing the orchestrator, scheduler, and dashboard integration.
"""

import time
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MockGUIEngine:
    """Simulates GUIEngine without actually controlling Housoft."""

    def __init__(self, fast_mode=True):
        """
        fast_mode=True  -> simulated actions take milliseconds (for quick tests)
        fast_mode=False -> realistic delays (to simulate real timing)
        """
        self.current_app = None
        self.current_module = None
        self.is_task_running = False
        self.fast_mode = fast_mode
        self.actions_log = []  # For test verification

        # Simulate state that changes over time (popups, errors)
        self._popup_probability = 0.02  # 2% chance per check
        logger.info(f"MockGUIEngine initialized (fast_mode={fast_mode})")

    def _delay(self, min_sec, max_sec):
        """Simulate a delay. Much faster in fast_mode."""
        if self.fast_mode:
            time.sleep(random.uniform(0.01, 0.05))
        else:
            time.sleep(random.uniform(min_sec, max_sec))

    def _log_action(self, action, details=""):
        """Record an action in the internal log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "current_app": self.current_app,
            "current_module": self.current_module,
        }
        self.actions_log.append(entry)
        logger.info(f"[MOCK] {action}: {details}")

    # ─── Window Management ───────────────────────────────────

    def find_window(self, app_name):
        """Simulate finding a Housoft window."""
        self._log_action("find_window", app_name)
        return f"MockWindow({app_name})"

    def bring_to_front(self, app_name):
        """Simulate focusing a window."""
        self._log_action("bring_to_front", app_name)
        self._delay(0.5, 1.0)
        self.current_app = app_name
        return True

    # ─── Task Control ────────────────────────────────────────

    def start_task(self, app_name, module_name):
        """Simulate starting a task."""
        self._log_action("start_task", f"{app_name}/{module_name}")

        # Simulate focus
        if not self.bring_to_front(app_name):
            return False
        self._delay(0.5, 1.0)

        # Simulate clicking module button
        self._log_action("click_module", module_name)
        self._delay(0.5, 1.5)

        # Simulate clicking OK
        self._log_action("click_ok")
        self._delay(0.3, 0.8)

        self.current_module = module_name
        self.is_task_running = True
        return True

    def stop_task(self):
        """Simulate stopping the current task."""
        if not self.is_task_running:
            self._log_action("stop_task", "no task running")
            return True

        self._log_action("stop_task", self.current_module)
        self._log_action("click_parar")
        self._delay(1.0, 2.0)

        self.is_task_running = False
        self.current_module = None
        return True

    def switch_task(self, app_name, module_name):
        """Simulate switching to a new task."""
        self._log_action("switch_task", f"{app_name}/{module_name}")

        if self.is_task_running:
            if not self.stop_task():
                return False
            self._delay(2.0, 4.0)

        return self.start_task(app_name, module_name)

    # ─── State Detection ─────────────────────────────────────

    def detect_popup(self):
        """Randomly simulate a popup appearing."""
        if random.random() < self._popup_probability:
            popup_type = random.choice(["popup_alert", "popup_blocked"])
            self._log_action("detect_popup", popup_type)
            return popup_type
        return None

    def dismiss_popup(self):
        """Simulate dismissing a popup."""
        self._log_action("dismiss_popup")
        self._delay(0.3, 0.8)
        return True

    def check_task_status(self):
        """Return current task status."""
        if self.is_task_running:
            return "running"
        return "stopped"

    # ─── Utility ─────────────────────────────────────────────

    def human_delay(self, min_sec=1.0, max_sec=3.0):
        """Simulate human-like delay."""
        self._delay(min_sec, max_sec)

    def take_screenshot(self):
        """Return a dummy screenshot placeholder."""
        return None

    def find_element(self, template_name, confidence=0.8):
        """Simulate finding an element."""
        self._log_action("find_element", template_name)
        # Simulate random position
        return (random.randint(100, 900), random.randint(100, 700))

    def click_element(self, template_name, confidence=0.8, retries=3):
        """Simulate clicking an element."""
        self._log_action("click_element", template_name)
        return True

    # ─── Test Helpers ────────────────────────────────────────

    def get_action_summary(self):
        """Return a summary of all actions performed."""
        summary = {}
        for entry in self.actions_log:
            action = entry["action"]
            summary[action] = summary.get(action, 0) + 1
        return summary

    def get_task_executions(self):
        """Return list of all task executions."""
        return [e for e in self.actions_log if e["action"] == "start_task"]

    def clear_log(self):
        """Clear the actions log."""
        self.actions_log = []
