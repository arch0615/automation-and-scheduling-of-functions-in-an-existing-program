"""
Install Housoft Meta as a Windows startup task.

Creates a Windows Task Scheduler entry that:
  - Runs watchdog.py at user logon
  - Runs in the background (no console window)
  - Restarts automatically on failure
"""
import os
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
WATCHDOG_SCRIPT = SCRIPT_DIR / "watchdog.py"
TASK_NAME = "HousoftMetaAutomation"


def find_python():
    """Find a Python executable that works."""
    for cmd in ["pyw", "py", "python"]:
        try:
            result = subprocess.run([cmd, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                return cmd
        except FileNotFoundError:
            continue
    return sys.executable


def install_task():
    """Create a scheduled task that runs at logon."""
    python = find_python()

    # Build command for Task Scheduler
    cmd = [
        "schtasks", "/Create",
        "/TN", TASK_NAME,
        "/TR", f'"{python}" "{WATCHDOG_SCRIPT}"',
        "/SC", "ONLOGON",
        "/RL", "HIGHEST",
        "/F",  # force overwrite if exists
    ]

    print(f"Installing auto-start task '{TASK_NAME}'...")
    print(f"Python: {python}")
    print(f"Script: {WATCHDOG_SCRIPT}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"\n[OK] Task '{TASK_NAME}' installed successfully")
        print("   The Housoft Meta system will start automatically at logon.")
        print(f"\n   To start it now without rebooting:")
        print(f"   schtasks /Run /TN \"{TASK_NAME}\"")
    else:
        print(f"\n[ERROR] Failed to install task:")
        print(result.stderr)
        return False
    return True


def uninstall_task():
    """Remove the scheduled task."""
    cmd = ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[OK] Task '{TASK_NAME}' removed")
        return True
    print(f"[ERROR] Failed to remove task: {result.stderr}")
    return False


def check_task():
    """Check if the task is installed."""
    cmd = ["schtasks", "/Query", "/TN", TASK_NAME]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        uninstall_task()
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        if check_task():
            print(f"[OK] Task '{TASK_NAME}' is installed")
        else:
            print(f"[NOT FOUND] Task '{TASK_NAME}' is not installed")
        return

    # Check admin privileges (schtasks needs admin for HIGHEST run level)
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        is_admin = False

    if not is_admin:
        print("WARNING: This script should be run as Administrator to use /RL HIGHEST.")
        print("         Re-run from an elevated command prompt if installation fails.\n")

    install_task()


if __name__ == "__main__":
    main()
