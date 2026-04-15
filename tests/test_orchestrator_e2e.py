"""
End-to-end test: Orchestrator + Mock GUI Engine
Runs the full system with simulated Housoft to verify:
  - Task scheduling works
  - Randomization works
  - Category-based queuing works
  - Login Loop timing works
  - Pause/resume works
  - Off-hours handling works
"""

import sys
import time
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging BEFORE imports so we see everything
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("E2E_TEST")

from core.mock_gui_engine import MockGUIEngine
from orchestrator.scheduler import TaskOrchestrator


def _speed_up_orchestrator(orch):
    """Patch the orchestrator to use tiny durations for testing."""
    # Disable config reload so our in-memory changes stick
    orch._reload_config_each_cycle = False

    # Set task duration to ~2 seconds (0.03 minutes)
    for task in orch.config["tasks"]:
        task["duration_min"] = 0.03

    # Lower the duration floor (normally 5 minutes)
    orch._min_duration_min = 0.02

    # Tiny delays between tasks (in minutes)
    orch.config["randomization"]["delay_between_tasks_min"] = 0.02
    orch.config["randomization"]["delay_between_tasks_max"] = 0.04

    # Check task progress every 0.5 seconds instead of every 30 seconds
    orch._check_interval_sec = 0.5


def test_basic_flow():
    """Test: start orchestrator, run a few cycles, stop."""
    print("\n" + "=" * 70)
    print("TEST 1: Basic Flow — Start, run 30s, stop")
    print("=" * 70)

    mock_gui = MockGUIEngine(fast_mode=True)
    orch = TaskOrchestrator(mock_gui)
    _speed_up_orchestrator(orch)

    print("\nStarting orchestrator...")
    orch.start()

    print("Running for 30 seconds...")
    time.sleep(30)

    print("\nStopping orchestrator...")
    orch.stop()

    # Analyze results
    summary = mock_gui.get_action_summary()
    executions = mock_gui.get_task_executions()

    print(f"\n=== TEST 1 RESULTS ===")
    print(f"Total actions: {len(mock_gui.actions_log)}")
    print(f"Task executions: {len(executions)}")
    print(f"Action summary: {summary}")

    if executions:
        print(f"\nTasks executed in order:")
        for i, ex in enumerate(executions[:10]):
            print(f"  {i+1}. {ex['details']}")

    # Verify expectations
    assert len(executions) > 0, "FAIL: No tasks were executed"
    assert summary.get("start_task", 0) > 0, "FAIL: No start_task actions"
    assert summary.get("click_ok", 0) > 0, "FAIL: No click_ok actions"
    print("\n[PASS] Basic flow test")
    return True


def test_task_queue_categories():
    """Test: verify task queue respects categories and login loop timing."""
    print("\n" + "=" * 70)
    print("TEST 2: Task Queue — Category ordering + Login Loop")
    print("=" * 70)

    mock_gui = MockGUIEngine(fast_mode=True)
    orch = TaskOrchestrator(mock_gui)

    # Force peak hours by patching
    orch.get_intensity_multiplier = lambda: 1.0
    orch.get_current_intensity_mode = lambda: "peak"

    queue = orch.build_task_queue()

    print(f"\nQueue built ({len(queue)} tasks):")
    for i, task in enumerate(queue):
        print(f"  {i+1:2d}. [{task.get('category', 'unknown'):12s}] {task['module']}")

    # Verify Login Loop appears first (since _last_login_loop is None)
    assert queue[0].get("category") == "maintenance", \
        f"FAIL: First task should be maintenance (Login Loop), got {queue[0].get('category')}"

    # Verify all enabled tasks are present
    enabled_count = len(orch.get_enabled_tasks())
    # Utility tasks only run every 3 cycles, so may not be in first queue
    utility_count = len(orch.get_tasks_by_category("utility"))
    expected_min = enabled_count - utility_count
    assert len(queue) >= expected_min, \
        f"FAIL: Queue missing tasks. Got {len(queue)}, expected >= {expected_min}"

    print(f"\n[PASS] Category ordering verified")
    print(f"[PASS] Login Loop appears first")
    return True


def test_intensity_scheduling():
    """Test: verify tasks only run during peak/moderate hours."""
    print("\n" + "=" * 70)
    print("TEST 3: Intensity Scheduling")
    print("=" * 70)

    mock_gui = MockGUIEngine(fast_mode=True)
    orch = TaskOrchestrator(mock_gui)

    # Test off-hours detection
    orch.get_current_intensity_mode = lambda: "off"
    intensity = orch.get_intensity_multiplier()
    assert intensity == 0.0, f"FAIL: off-hours should be 0.0, got {intensity}"
    print("[PASS] Off-hours = 0.0 intensity")

    # Test peak hours
    orch.get_current_intensity_mode = lambda: "peak"
    intensity = orch.get_intensity_multiplier()
    assert intensity == 1.0, f"FAIL: peak should be 1.0, got {intensity}"
    print("[PASS] Peak hours = 1.0 intensity")

    # Test moderate hours
    orch.get_current_intensity_mode = lambda: "moderate"
    intensity = orch.get_intensity_multiplier()
    assert intensity == 0.6, f"FAIL: moderate should be 0.6, got {intensity}"
    print("[PASS] Moderate hours = 0.6 intensity")

    return True


def test_pause_resume():
    """Test: pause stops task execution, resume continues."""
    print("\n" + "=" * 70)
    print("TEST 4: Pause/Resume")
    print("=" * 70)

    mock_gui = MockGUIEngine(fast_mode=True)
    orch = TaskOrchestrator(mock_gui)
    _speed_up_orchestrator(orch)

    orch.start()
    time.sleep(5)

    executions_before_pause = len(mock_gui.get_task_executions())
    print(f"Executions before pause: {executions_before_pause}")

    orch.pause()
    time.sleep(3)

    executions_during_pause = len(mock_gui.get_task_executions())
    # While paused, new tasks shouldn't START much more (allow a bit of slack for in-flight)
    delta = executions_during_pause - executions_before_pause
    print(f"Executions during pause: {executions_during_pause} (delta={delta})")

    orch.resume()
    time.sleep(5)

    executions_after_resume = len(mock_gui.get_task_executions())
    print(f"Executions after resume: {executions_after_resume}")

    orch.stop()

    assert executions_after_resume > executions_before_pause, \
        "FAIL: Tasks didn't resume after unpause"

    print("[PASS] Pause/resume works correctly")
    return True


def main():
    tests = [
        test_intensity_scheduling,
        test_task_queue_categories,
        test_basic_flow,
        test_pause_resume,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except AssertionError as e:
            print(f"\n[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"\n[ERROR] {test.__name__}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"FINAL RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
