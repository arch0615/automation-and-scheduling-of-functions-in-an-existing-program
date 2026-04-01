"""
Housoft Meta-Automation System
Main entry point - starts the GUI engine, orchestrator, and web dashboard.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

# Configure logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

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

    # Initialize GUI Engine
    from core.gui_engine import GUIEngine
    gui = GUIEngine()

    # Initialize Orchestrator
    from orchestrator.scheduler import TaskOrchestrator
    orchestrator = TaskOrchestrator(gui)

    # Save default config if none exists
    if not orchestrator.CONFIG_PATH.exists():
        orchestrator.save_config()
        logger.info("Default config saved")

    # Initialize Web Dashboard
    from web.app import create_app
    app = create_app(orchestrator)

    port = int(os.getenv("FLASK_PORT", 5000))

    # Start ngrok tunnel for mobile access
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

    # Start Flask server
    logger.info(f"Starting web dashboard on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
