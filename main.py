"""
Housoft Meta-Automation System
Main entry point - starts the GUI engine, orchestrator, and web dashboard.
"""

import os
import sys
import logging

from core.app_paths import load_env_file, logs_dir

load_env_file()

LOG_DIR = logs_dir()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "housoft_meta.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def main():
    """Start the Housoft Meta-Automation System."""
    logger.info("=" * 60)
    logger.info("Housoft Meta-Automation System starting...")
    logger.info("=" * 60)

    from core.vision_engine import VisionGUIEngine
    gui = VisionGUIEngine()

    # Bring Housoft to the front at startup so the user can see it's running
    # and so the first task interaction doesn't fight the browser for focus.
    # We don't fail if Housoft isn't open yet — the user may still be launching it.
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

    logger.info(f"Starting web dashboard on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
