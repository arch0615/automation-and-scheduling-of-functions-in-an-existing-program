"""
Watchdog — Supervises the Housoft Meta system.

Automatically restarts main.py if it crashes, logs all events,
and sends alerts after N consecutive failures.
"""
import os
import sys
import time
import signal
import logging
import subprocess
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHDOG] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "watchdog.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

MAIN_SCRIPT = SCRIPT_DIR / "main.py"
RESTART_DELAY_SEC = 10
MAX_FAILURES_BEFORE_ALERT = 5
FAILURE_RESET_WINDOW_SEC = 3600  # 1 hour


class Watchdog:
    def __init__(self):
        self.process = None
        self.consecutive_failures = 0
        self.first_failure_time = None
        self.total_restarts = 0
        self.should_run = True

    def _handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.should_run = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except Exception:
                self.process.kill()

    def _start_main(self):
        """Start the main.py process."""
        logger.info(f"Starting main.py (restart #{self.total_restarts + 1})")
        try:
            # Use pythonw or py depending on what's available
            python_cmd = self._find_python()
            self.process = subprocess.Popen(
                [python_cmd, str(MAIN_SCRIPT)],
                cwd=str(SCRIPT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            logger.info(f"Main process started (PID: {self.process.pid})")
            return True
        except Exception as e:
            logger.error(f"Failed to start main.py: {e}")
            return False

    def _find_python(self):
        """Find the Python executable."""
        for cmd in ["py", "python", "python3"]:
            try:
                subprocess.run([cmd, "--version"], capture_output=True, check=True)
                return cmd
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        return sys.executable

    def _check_failure_window(self):
        """Reset failure count if enough time has passed."""
        if self.first_failure_time:
            elapsed = (datetime.now() - self.first_failure_time).total_seconds()
            if elapsed > FAILURE_RESET_WINDOW_SEC:
                logger.info("Failure window expired, resetting counter")
                self.consecutive_failures = 0
                self.first_failure_time = None

    def _handle_failure(self):
        """Handle a process crash."""
        if self.consecutive_failures == 0:
            self.first_failure_time = datetime.now()
        self.consecutive_failures += 1
        self.total_restarts += 1

        logger.warning(
            f"Process crashed. Consecutive failures: {self.consecutive_failures} "
            f"(total restarts: {self.total_restarts})"
        )

        if self.consecutive_failures >= MAX_FAILURES_BEFORE_ALERT:
            logger.error(
                f"ALERT: {self.consecutive_failures} consecutive failures! "
                f"Main.py may have a persistent issue. Still retrying..."
            )
            # Could send email/telegram alert here in future

    def run(self):
        """Main supervisor loop."""
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info("=" * 60)
        logger.info("Housoft Meta Watchdog started")
        logger.info(f"Supervising: {MAIN_SCRIPT}")
        logger.info("=" * 60)

        while self.should_run:
            if not self._start_main():
                logger.error(f"Failed to start, retrying in {RESTART_DELAY_SEC}s...")
                time.sleep(RESTART_DELAY_SEC)
                continue

            # Stream output from child process
            try:
                for line in self.process.stdout:
                    logger.info(f"[main] {line.rstrip()}")
            except Exception as e:
                logger.error(f"Error reading process output: {e}")

            # Process has exited
            return_code = self.process.wait()

            if not self.should_run:
                logger.info("Shutdown requested, exiting")
                break

            if return_code == 0:
                logger.info("Main process exited cleanly")
                self.consecutive_failures = 0
            else:
                logger.warning(f"Main process exited with code {return_code}")
                self._handle_failure()

            self._check_failure_window()

            if self.should_run:
                logger.info(f"Restarting in {RESTART_DELAY_SEC} seconds...")
                time.sleep(RESTART_DELAY_SEC)

        logger.info("Watchdog stopped")


if __name__ == "__main__":
    watchdog = Watchdog()
    watchdog.run()
