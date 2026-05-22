"""
Housoft Meta-Automation System
Main entry point - starts the GUI engine, orchestrator, and web dashboard.
"""

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


def _crash_log_path() -> Path:
    """Where to put crash.log. Works in both frozen .exe and source-tree modes."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parent
    logs = base / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs / "crash.log"


def _write_crash_log(exc_info) -> Path | None:
    """Best-effort traceback writer — doesn't depend on app_paths or logging."""
    try:
        path = _crash_log_path()
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n\n=== Crash at {datetime.now().isoformat()} ===\n")
            f.write("".join(traceback.format_exception(*exc_info)))
            f.write(f"\nsys.executable: {sys.executable}\n")
            f.write(f"sys.frozen: {getattr(sys, 'frozen', False)}\n")
            f.write(f"sys.version: {sys.version}\n")
            f.write(f"cwd: {os.getcwd()}\n")
        return path
    except Exception:
        return None


def _wait_for_user_or_timeout(timeout_sec: float = 60.0) -> None:
    """Block until the user presses Enter or the timeout expires.

    Frozen apps run in a transient console window that closes on exit; this
    keeps it open long enough for the user to read the traceback.
    """
    import threading
    done = threading.Event()

    def _wait():
        try:
            input()
        except Exception:
            pass
        done.set()

    threading.Thread(target=_wait, daemon=True).start()
    done.wait(timeout=timeout_sec)


def _run() -> None:
    """The real startup. Wrapped by main() with crash handling."""
    import logging

    from core.app_paths import load_env_file, logs_dir

    load_env_file()
    log_dir = logs_dir()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "housoft_meta.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Housoft Meta-Automation System starting...")
    logger.info("=" * 60)

    from core.vision_engine import VisionGUIEngine
    gui = VisionGUIEngine()

    if gui.ensure_foreground("face"):
        logger.info("Housoft Face brought to foreground")
    else:
        logger.warning("Could not bring Housoft Face to foreground — make sure it's running")

    from orchestrator.scheduler import TaskOrchestrator
    orchestrator = TaskOrchestrator(gui)

    if not orchestrator.CONFIG_PATH.exists():
        orchestrator.save_config()
        logger.info("Default config saved")

    from web.app import create_app
    app = create_app(orchestrator)

    port = int(os.getenv("FLASK_PORT", 5000))

    ngrok_url = None
    try:
        from pyngrok import ngrok
        ngrok_url = ngrok.connect(port, "http").public_url
        logger.info(f"ngrok tunnel: {ngrok_url}")
        print(f"\n{'=' * 50}")
        print(f"  MOBILE ACCESS URL: {ngrok_url}")
        print(f"  Local URL: http://localhost:{port}")
        print(f"{'=' * 50}\n")
    except Exception as e:
        logger.warning(f"ngrok failed (dashboard will only be accessible locally): {e}")
        print(f"\n  Local URL: http://localhost:{port}\n")

    # Auto-open the dashboard in the user's default browser shortly after
    # app.run() binds. The Timer thread is scheduled BEFORE app.run() so it
    # fires while Flask is already serving requests.
    if os.getenv("AUTO_OPEN_BROWSER", "true").lower() in ("1", "true", "yes", "sim"):
        import threading
        import webbrowser
        url = f"http://localhost:{port}"

        def _open_browser():
            try:
                webbrowser.open(url)
            except Exception as exc:
                logger.warning(f"Could not auto-open browser: {exc}")

        threading.Timer(3.0, _open_browser).start()
        logger.info(f"Browser will open automatically at {url}")

    logger.info(f"Starting web dashboard on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)


def main() -> None:
    try:
        _run()
    except SystemExit:
        raise
    except BaseException:
        tb = traceback.format_exc()
        path = _write_crash_log(sys.exc_info())

        # Print the error to the console (which the wrapper will keep open).
        print()
        print("=" * 60)
        print("ERRO: Housoft Meta falhou ao iniciar.")
        print("ERROR: Housoft Meta failed to start.")
        print("=" * 60)
        print(tb)
        if path:
            print(f"Traceback completo salvo em: {path}")
            print(f"Full traceback written to:   {path}")
        print()
        print("Pressione Enter para sair (ou aguarde 60 segundos).")
        print("Press Enter to exit (or wait 60 seconds).")
        _wait_for_user_or_timeout(60.0)
        sys.exit(1)


if __name__ == "__main__":
    main()
