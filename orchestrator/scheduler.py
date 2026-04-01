"""
Task Scheduler & Orchestrator
Manages task sequencing, randomization, intensity control, and time-based scheduling.
"""

import time
import random
import logging
import json
from datetime import datetime
from pathlib import Path
from threading import Thread, Event

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """Orchestrates Housoft tasks based on schedule and randomization rules."""

    CONFIG_PATH = Path(__file__).parent.parent / "config" / "schedule.json"

    def __init__(self, gui_engine):
        self.gui = gui_engine
        self.config = self._load_config()
        self.is_running = False
        self.is_paused = False
        self._stop_event = Event()
        self._thread = None
        self.current_task = None
        self.task_history = []
        logger.info("TaskOrchestrator initialized")

    # ─── Config ──────────────────────────────────────────────

    def _load_config(self):
        """Load schedule configuration from JSON file."""
        if self.CONFIG_PATH.exists():
            with open(self.CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.info("Config loaded from file")
                return config
        else:
            logger.info("No config file found, using defaults")
            return self._default_config()

    def _default_config(self):
        """Return default configuration."""
        return {
            "tasks": [
                {"app": "insta", "module": "enviar_direct", "duration_min": 45, "targeting": "local", "enabled": True},
                {"app": "face", "module": "entrar_em_grupos", "duration_min": 30, "targeting": "local", "enabled": True},
                {"app": "face", "module": "postar_nos_grupos", "duration_min": 40, "targeting": "national", "enabled": True},
                {"app": "face", "module": "curtir_pagina", "duration_min": 20, "targeting": "national", "enabled": True},
                {"app": "face", "module": "comentar_publicacao", "duration_min": 25, "targeting": "local", "enabled": True},
                {"app": "face", "module": "enviar_mensagem", "duration_min": 35, "targeting": "local", "enabled": True},
            ],
            "schedule": {
                "peak_hours": [["08:00", "12:00"], ["14:00", "18:00"]],
                "moderate_hours": [["12:00", "14:00"], ["18:00", "22:00"]],
                "off_hours": [["22:00", "08:00"]]
            },
            "randomization": {
                "delay_between_tasks_min": 3,
                "delay_between_tasks_max": 10,
                "shuffle_task_order": True,
                "vary_duration_percent": 20
            },
            "intensity": {
                "peak": 1.0,
                "moderate": 0.6,
                "off": 0.0
            }
        }

    def save_config(self):
        """Save current config to file."""
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        logger.info("Config saved to file")

    def update_config(self, new_config):
        """Update configuration and save."""
        self.config.update(new_config)
        self.save_config()
        logger.info("Config updated")

    # ─── Time & Intensity ────────────────────────────────────

    def get_current_intensity_mode(self):
        """Determine current intensity mode based on time of day."""
        now = datetime.now().strftime("%H:%M")

        for period in self.config["schedule"]["peak_hours"]:
            if self._time_in_range(now, period[0], period[1]):
                return "peak"

        for period in self.config["schedule"]["moderate_hours"]:
            if self._time_in_range(now, period[0], period[1]):
                return "moderate"

        return "off"

    def _time_in_range(self, current, start, end):
        """Check if current time is within a range (handles overnight ranges)."""
        if start <= end:
            return start <= current <= end
        else:
            return current >= start or current <= end

    def get_intensity_multiplier(self):
        """Get the intensity multiplier for current time period."""
        mode = self.get_current_intensity_mode()
        return self.config["intensity"].get(mode, 0.0)

    # ─── Task Queue ──────────────────────────────────────────

    def get_enabled_tasks(self):
        """Return list of enabled tasks."""
        return [t for t in self.config["tasks"] if t.get("enabled", True)]

    def build_task_queue(self):
        """Build a randomized queue of tasks for the current cycle."""
        tasks = self.get_enabled_tasks()

        if self.config["randomization"]["shuffle_task_order"]:
            random.shuffle(tasks)

        logger.info(f"Task queue built: {[t['module'] for t in tasks]}")
        return tasks

    def get_task_duration(self, task):
        """Get randomized duration for a task (in minutes)."""
        base_duration = task["duration_min"]
        vary_percent = self.config["randomization"]["vary_duration_percent"]
        variation = base_duration * (vary_percent / 100)
        duration = random.uniform(base_duration - variation, base_duration + variation)

        # Apply intensity multiplier
        intensity = self.get_intensity_multiplier()
        duration *= intensity

        return max(5, duration)  # Minimum 5 minutes

    def get_delay_between_tasks(self):
        """Get random delay between task switches (in minutes)."""
        r = self.config["randomization"]
        return random.uniform(r["delay_between_tasks_min"], r["delay_between_tasks_max"])

    # ─── Main Loop ───────────────────────────────────────────

    def start(self):
        """Start the orchestrator in a background thread."""
        if self.is_running:
            logger.warning("Orchestrator is already running")
            return

        self._stop_event.clear()
        self.is_running = True
        self.is_paused = False
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Orchestrator started")

    def stop(self):
        """Stop the orchestrator."""
        logger.info("Stopping orchestrator...")
        self._stop_event.set()
        self.is_running = False

        # Stop any running task in Housoft
        self.gui.stop_task()

        if self._thread:
            self._thread.join(timeout=10)

        self.current_task = None
        logger.info("Orchestrator stopped")

    def pause(self):
        """Pause the orchestrator."""
        self.is_paused = True
        logger.info("Orchestrator paused")

    def resume(self):
        """Resume the orchestrator."""
        self.is_paused = False
        logger.info("Orchestrator resumed")

    def _run_loop(self):
        """Main orchestration loop. Runs in background thread."""
        logger.info("Orchestration loop started")

        while not self._stop_event.is_set():
            # Check if we should be active
            intensity = self.get_intensity_multiplier()
            if intensity == 0:
                mode = self.get_current_intensity_mode()
                logger.info(f"Off-hours ({mode}), sleeping for 5 minutes...")
                self._sleep(300)  # Check again in 5 minutes
                continue

            # Check if paused
            if self.is_paused:
                logger.debug("Orchestrator is paused")
                self._sleep(10)
                continue

            # Build and execute task queue
            task_queue = self.build_task_queue()

            for task in task_queue:
                if self._stop_event.is_set():
                    break

                # Skip if paused
                while self.is_paused and not self._stop_event.is_set():
                    self._sleep(5)

                if self._stop_event.is_set():
                    break

                # Execute task
                self._execute_task(task)

                # Delay between tasks
                if not self._stop_event.is_set():
                    delay = self.get_delay_between_tasks()
                    logger.info(f"Waiting {delay:.1f} minutes before next task")
                    self._sleep(delay * 60)

        logger.info("Orchestration loop ended")

    def _execute_task(self, task):
        """Execute a single task for its configured duration."""
        self.current_task = task
        module_name = task["module"]
        app_name = task["app"]
        duration = self.get_task_duration(task)

        logger.info(f"Executing: {app_name}/{module_name} for {duration:.0f} minutes")

        # Record in history
        self.task_history.append({
            "task": module_name,
            "app": app_name,
            "started_at": datetime.now().isoformat(),
            "planned_duration_min": duration,
            "status": "started"
        })

        # Keep only last 50 history entries
        if len(self.task_history) > 50:
            self.task_history = self.task_history[-50:]

        # Start the task via GUI
        success = self.gui.switch_task(app_name, module_name)

        if not success:
            logger.error(f"Failed to start task: {module_name}")
            self.task_history[-1]["status"] = "failed"
            self.current_task = None
            return

        self.task_history[-1]["status"] = "running"

        # Wait for task duration
        end_time = time.time() + (duration * 60)
        while time.time() < end_time and not self._stop_event.is_set():
            # Check for popups periodically
            popup = self.gui.detect_popup()
            if popup:
                logger.warning(f"Popup detected during task: {popup}")
                self.gui.dismiss_popup()

            self._sleep(30)  # Check every 30 seconds

        # Stop the task
        if not self._stop_event.is_set():
            self.gui.stop_task()
            self.task_history[-1]["status"] = "completed"
            logger.info(f"Task completed: {module_name}")

        self.current_task = None

    def _sleep(self, seconds):
        """Sleep that can be interrupted by stop event."""
        self._stop_event.wait(timeout=seconds)

    # ─── Status ──────────────────────────────────────────────

    def get_status(self):
        """Return current status for the dashboard."""
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "current_task": self.current_task,
            "intensity_mode": self.get_current_intensity_mode(),
            "intensity_multiplier": self.get_intensity_multiplier(),
            "task_history": self.task_history[-10:],
            "enabled_tasks_count": len(self.get_enabled_tasks()),
            "timestamp": datetime.now().isoformat()
        }
