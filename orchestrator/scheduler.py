"""
Task Scheduler & Orchestrator
Manages task sequencing, randomization, intensity control, and time-based scheduling.
Supports 12 Facebook modules + Instagram modules with category-based ordering.
"""

import time
import random
import logging
import json
from datetime import datetime
from threading import Thread, Event

from core.app_paths import config_dir

logger = logging.getLogger(__name__)


# Task categories control execution order and grouping
CATEGORY_PRIORITY = {
    "maintenance": 0,   # Login Loop — runs first to warm up accounts
    "growth": 1,        # Entrar em Grupos, Adicionar Amigos
    "posting": 2,       # Postar nos Grupos, Mural, Marketplace, Aniversariantes
    "messaging": 3,     # Enviar Mensagem, Responder Mensagem, Enviar Direct
    "engagement": 4,    # Curtir, Compartilhar, Paginas e Eventos
    "utility": 5,       # Criar Lista — runs periodically, not every cycle
}


class TaskOrchestrator:
    """Orchestrates Housoft tasks based on schedule and randomization rules."""

    CONFIG_PATH = config_dir() / "schedule.json"

    def __init__(self, gui_engine):
        self.gui = gui_engine
        self.config = self._load_config()
        self.is_running = False
        self.is_paused = False
        self._stop_event = Event()
        self._thread = None
        self.current_task = None
        self.task_history = []
        self._cycle_count = 0
        self._last_login_loop = None
        self._check_interval_sec = 30  # How often to check within a task (patched for tests)
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
                {"app": "face", "module": "postar_nos_grupos", "display_name": "Postar nos Grupos", "duration_min": 40, "targeting": "national", "category": "posting", "enabled": True},
                {"app": "face", "module": "postar_no_mural", "display_name": "Postar no Mural", "duration_min": 30, "targeting": "local", "category": "posting", "enabled": True},
                {"app": "face", "module": "enviar_mensagem", "display_name": "Enviar Mensagem", "duration_min": 35, "targeting": "local", "category": "messaging", "enabled": True},
                {"app": "face", "module": "entrar_em_grupos", "display_name": "Entrar em Grupos", "duration_min": 25, "targeting": "local", "category": "growth", "enabled": True},
                {"app": "face", "module": "curtir", "display_name": "Curtir", "duration_min": 20, "targeting": "national", "category": "engagement", "enabled": True},
                {"app": "insta", "module": "enviar_direct", "display_name": "Enviar Direct", "duration_min": 45, "targeting": "local", "category": "messaging", "enabled": True},
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
            },
            "login_loop_settings": {
                "run_every_hours": 4,
                "do_not_interrupt": True
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

    def reload_config(self):
        """Reload configuration from file."""
        self.config = self._load_config()
        logger.info("Config reloaded")

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

    def get_tasks_by_category(self, category):
        """Return enabled tasks filtered by category."""
        return [t for t in self.get_enabled_tasks() if t.get("category") == category]

    def _should_run_login_loop(self):
        """Check if it's time to run the Login Loop based on configured interval."""
        settings = self.config.get("login_loop_settings", {})
        interval_hours = settings.get("run_every_hours", 4)

        if self._last_login_loop is None:
            return True

        elapsed = (datetime.now() - self._last_login_loop).total_seconds() / 3600
        return elapsed >= interval_hours

    def build_task_queue(self):
        """
        Build a smart task queue for the current cycle.
        - Groups tasks by category
        - Shuffles within each category
        - Interleaves categories for natural behavior
        - Inserts Login Loop periodically
        - Runs utility tasks (Criar Lista) only every few cycles
        """
        enabled_tasks = self.get_enabled_tasks()

        # Separate Login Loop and utility tasks from regular tasks
        regular_tasks = [t for t in enabled_tasks if t.get("category") not in ("maintenance", "utility")]
        login_loop_tasks = [t for t in enabled_tasks if t.get("category") == "maintenance"]
        utility_tasks = [t for t in enabled_tasks if t.get("category") == "utility"]

        # Build queue starting with Login Loop if due
        queue = []

        if login_loop_tasks and self._should_run_login_loop():
            queue.extend(login_loop_tasks)
            logger.info("Login Loop added to queue (periodic maintenance)")

        # Group regular tasks by category and shuffle within each group
        category_groups = {}
        for task in regular_tasks:
            cat = task.get("category", "posting")
            if cat not in category_groups:
                category_groups[cat] = []
            category_groups[cat].append(task)

        # Shuffle within each category
        for cat in category_groups:
            random.shuffle(category_groups[cat])

        # Interleave categories: pick one task from each category in rotation
        if self.config["randomization"]["shuffle_task_order"]:
            # Randomized interleaving
            sorted_categories = sorted(category_groups.keys(),
                                       key=lambda c: CATEGORY_PRIORITY.get(c, 99))
            while any(category_groups[c] for c in sorted_categories if c in category_groups):
                for cat in sorted_categories:
                    if cat in category_groups and category_groups[cat]:
                        queue.append(category_groups[cat].pop(0))
        else:
            # Sequential by category priority
            for cat in sorted(category_groups.keys(),
                              key=lambda c: CATEGORY_PRIORITY.get(c, 99)):
                queue.extend(category_groups[cat])

        # Add utility tasks every 3 cycles
        if utility_tasks and self._cycle_count % 3 == 0:
            queue.extend(utility_tasks)
            logger.info("Utility tasks added to queue (periodic)")

        logger.info(f"Task queue built ({len(queue)} tasks): {[t['module'] for t in queue]}")
        return queue

    # Minimum duration floor (seconds equivalent of 5 min default). Tests may lower this.
    _min_duration_min = 5
    # Whether to reload config from file on each cycle (disable for tests)
    _reload_config_each_cycle = True

    def get_task_duration(self, task):
        """Get randomized duration for a task (in minutes)."""
        base_duration = task["duration_min"]
        vary_percent = self.config["randomization"]["vary_duration_percent"]
        variation = base_duration * (vary_percent / 100)
        duration = random.uniform(base_duration - variation, base_duration + variation)

        # Apply intensity multiplier (except for maintenance tasks)
        if task.get("category") != "maintenance":
            intensity = self.get_intensity_multiplier()
            duration *= intensity

        return max(self._min_duration_min, duration)

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

            # Reload config in case it was changed via dashboard
            if self._reload_config_each_cycle:
                self.reload_config()

            # Build and execute task queue for this cycle
            self._cycle_count += 1
            task_queue = self.build_task_queue()

            for task in task_queue:
                if self._stop_event.is_set():
                    break

                # Skip if paused
                while self.is_paused and not self._stop_event.is_set():
                    self._sleep(5)

                if self._stop_event.is_set():
                    break

                # Re-check intensity (time may have changed during cycle)
                if self.get_intensity_multiplier() == 0:
                    logger.info("Entered off-hours during cycle, stopping tasks")
                    break

                # Execute task
                self._execute_task(task)

                # Delay between tasks (skip delay after Login Loop if configured)
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
        display_name = task.get("display_name", module_name)
        category = task.get("category", "unknown")
        duration = self.get_task_duration(task)

        logger.info(f"Executing: [{category}] {app_name}/{display_name} for {duration:.0f} minutes")

        # Record in history
        self.task_history.append({
            "task": module_name,
            "display_name": display_name,
            "app": app_name,
            "category": category,
            "targeting": task.get("targeting", "local"),
            "started_at": datetime.now().isoformat(),
            "planned_duration_min": round(duration, 1),
            "status": "started"
        })

        # Keep only last 50 history entries
        if len(self.task_history) > 50:
            self.task_history = self.task_history[-50:]

        # Track Login Loop timing
        if category == "maintenance":
            self._last_login_loop = datetime.now()

        # Build the runtime context (dynamic values consumed by the start sequence —
        # e.g. the rotating search keyword for entrar_em_grupos).
        context = self._build_task_context(task)

        # Start the task via GUI
        success = self.gui.switch_task(app_name, module_name, context=context)

        if not success:
            logger.error(f"Failed to start task: {display_name}")
            self.task_history[-1]["status"] = "failed"
            self.current_task = None
            return

        self.task_history[-1]["status"] = "running"

        # Check if this task should not be interrupted (e.g., Login Loop)
        do_not_interrupt = (
            category == "maintenance"
            and self.config.get("login_loop_settings", {}).get("do_not_interrupt", True)
        )

        # Wait for task duration
        end_time = time.time() + (duration * 60)
        while time.time() < end_time and not self._stop_event.is_set():
            # Check for popups periodically
            popup = self.gui.detect_popup()
            if popup:
                logger.warning(f"Popup detected during task: {popup}")
                self.gui.dismiss_popup()

            # Don't break out of maintenance tasks even if paused
            if self.is_paused and not do_not_interrupt:
                break

            self._sleep(self._check_interval_sec)

        # Stop the task
        if not self._stop_event.is_set():
            self.gui.stop_task()
            self.task_history[-1]["status"] = "completed"
            self.task_history[-1]["completed_at"] = datetime.now().isoformat()
            logger.info(f"Task completed: {display_name}")

        self.current_task = None

    def _sleep(self, seconds):
        """Sleep that can be interrupted by stop event."""
        self._stop_event.wait(timeout=seconds)

    # ─── Per-task context (runtime parameters for click sequences) ──

    def _build_task_context(self, task):
        """Build a context dict for the click sequence to consume.

        For most modules this is empty. For modules that prompt for input
        (e.g. entrar_em_grupos's "Pesquisar" dialog), we inject a keyword
        rotated across cycles so the bot doesn't get stuck on an empty
        search field. Per-task `search_keywords` in schedule.json win over
        the per-module defaults in click_sequences.MODULE_SEQUENCES.
        """
        context = {}
        if task["module"] == "entrar_em_grupos":
            keywords = self._search_keywords_for(task)
            if keywords:
                term = keywords[self._cycle_count % len(keywords)]
                context["search_term"] = self._substitute_placeholders(term)
                logger.info(f"entrar_em_grupos search term for this cycle: {context['search_term']!r}")
            else:
                logger.warning("entrar_em_grupos has no search keywords configured — task may stall")
        return context

    def _search_keywords_for(self, task):
        """Resolve the keyword list for a task: task-level override → module default."""
        keywords = task.get("search_keywords")
        if keywords:
            return list(keywords)
        from core.click_sequences import get_targeting_config
        targeting_cfg = get_targeting_config(task["module"], task.get("targeting", "local"))
        return list(targeting_cfg.get("keywords", []))

    def _substitute_placeholders(self, term):
        """Replace [cidade] (and other config placeholders) inside a keyword string."""
        city = self.config.get("city", "")
        return term.replace("[cidade]", city).strip()

    # ─── Foreground management ──────────────────────────────

    def ensure_foreground(self, app_name="face"):
        """Bring Housoft to the foreground; safe to call from the web request thread.

        Used at app startup and whenever the user clicks Start in the dashboard,
        so the bot's first interaction isn't with whatever window happened to
        be on top (browser, Explorer, etc.).
        """
        if hasattr(self.gui, "ensure_foreground"):
            return self.gui.ensure_foreground(app_name)
        return self.gui.bring_to_front(app_name)

    # ─── Status ──────────────────────────────────────────────

    def get_status(self):
        """Return current status for the dashboard."""
        focus_status = None
        if hasattr(self.gui, "get_focus_status"):
            try:
                focus_status = self.gui.get_focus_status()
            except Exception as e:
                logger.warning(f"get_focus_status raised: {e}")
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "current_task": self.current_task,
            "intensity_mode": self.get_current_intensity_mode(),
            "intensity_multiplier": self.get_intensity_multiplier(),
            "task_history": self.task_history[-10:],
            "enabled_tasks_count": len(self.get_enabled_tasks()),
            "cycle_count": self._cycle_count,
            "focus_status": focus_status,
            "timestamp": datetime.now().isoformat()
        }
