"""
Flask Web Dashboard
Mobile-friendly control panel for monitoring and controlling the Housoft automation.
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")

# Will be set when the app starts
orchestrator = None

DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")


# ─── Authentication ──────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


# ─── Dashboard ───────────────────────────────────────────

@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")


# ─── API Endpoints ───────────────────────────────────────

@app.route("/api/status")
@login_required
def api_status():
    """Get current system status."""
    if orchestrator:
        return jsonify(orchestrator.get_status())
    return jsonify({"error": "Orchestrator not initialized"})


@app.route("/api/start", methods=["POST"])
@login_required
def api_start():
    """Start the orchestrator."""
    if orchestrator:
        orchestrator.start()
        return jsonify({"status": "started"})
    return jsonify({"error": "Orchestrator not initialized"}), 500


@app.route("/api/stop", methods=["POST"])
@login_required
def api_stop():
    """Stop the orchestrator."""
    if orchestrator:
        orchestrator.stop()
        return jsonify({"status": "stopped"})
    return jsonify({"error": "Orchestrator not initialized"}), 500


@app.route("/api/pause", methods=["POST"])
@login_required
def api_pause():
    """Pause the orchestrator."""
    if orchestrator:
        orchestrator.pause()
        return jsonify({"status": "paused"})
    return jsonify({"error": "Orchestrator not initialized"}), 500


@app.route("/api/resume", methods=["POST"])
@login_required
def api_resume():
    """Resume the orchestrator."""
    if orchestrator:
        orchestrator.resume()
        return jsonify({"status": "resumed"})
    return jsonify({"error": "Orchestrator not initialized"}), 500


@app.route("/api/schedule", methods=["GET"])
@login_required
def api_get_schedule():
    """Get current schedule config."""
    if orchestrator:
        return jsonify(orchestrator.config)
    return jsonify({"error": "Orchestrator not initialized"}), 500


@app.route("/api/schedule", methods=["POST"])
@login_required
def api_update_schedule():
    """Update schedule config."""
    if orchestrator:
        new_config = request.get_json()
        orchestrator.update_config(new_config)
        return jsonify({"status": "updated"})
    return jsonify({"error": "Orchestrator not initialized"}), 500


@app.route("/api/tasks", methods=["GET"])
@login_required
def api_get_tasks():
    """Get list of all tasks."""
    if orchestrator:
        return jsonify({"tasks": orchestrator.config.get("tasks", [])})
    return jsonify({"error": "Orchestrator not initialized"}), 500


@app.route("/api/tasks/<int:index>/toggle", methods=["POST"])
@login_required
def api_toggle_task(index):
    """Enable/disable a specific task."""
    if orchestrator:
        tasks = orchestrator.config.get("tasks", [])
        if 0 <= index < len(tasks):
            tasks[index]["enabled"] = not tasks[index].get("enabled", True)
            orchestrator.save_config()
            return jsonify({"status": "toggled", "task": tasks[index]})
        return jsonify({"error": "Invalid task index"}), 400
    return jsonify({"error": "Orchestrator not initialized"}), 500


@app.route("/api/history")
@login_required
def api_history():
    """Get task execution history."""
    if orchestrator:
        return jsonify({"history": orchestrator.task_history[-20:]})
    return jsonify({"error": "Orchestrator not initialized"}), 500


def set_orchestrator(orch):
    """Set the orchestrator instance for the web app."""
    global orchestrator
    orchestrator = orch


def create_app(orch=None):
    """Create and configure the Flask app."""
    if orch:
        set_orchestrator(orch)
    return app
