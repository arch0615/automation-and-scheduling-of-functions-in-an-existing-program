# Housoft Meta - User Guide

**Housoft Meta** is an automation and scheduling system for Housoft Face and Housoft Instagram applications. It automates repetitive tasks using image recognition, provides intelligent time-based scheduling, and offers a mobile-friendly web dashboard for monitoring and control.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Starting the Application](#starting-the-application)
5. [Web Dashboard](#web-dashboard)
6. [Task Management](#task-management)
7. [Scheduling & Intensity](#scheduling--intensity)
8. [Remote Access (Mobile)](#remote-access-mobile)
9. [API Reference](#api-reference)
10. [Safety Features](#safety-features)
11. [Troubleshooting](#troubleshooting)
12. [Project Structure](#project-structure)

---

## System Requirements

- **OS:** Windows 10 or later
- **Python:** 3.8+
- **Applications:** Housoft Face and/or Housoft Instagram installed and running
- **Display:** The Housoft application windows must be visible on screen (not minimized behind other windows during automation)
- **Network:** Internet connection (required for ngrok remote access)

---

## Installation

### 1. Clone or download the project

Place the `housoft-meta` folder in your preferred location.

### 2. Create a virtual environment (recommended)

```bash
cd housoft-meta
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed:**

| Package | Purpose |
|---------|---------|
| pyautogui | Mouse and keyboard automation |
| pywinauto | Windows window management |
| opencv-python | Image recognition for UI elements |
| pillow | Image processing |
| flask | Web dashboard server |
| flask-login | Session-based authentication |
| apscheduler | Advanced scheduling |
| pyngrok | Remote access tunnel |
| requests | HTTP client |
| python-dotenv | Environment variable loading |

---

## Configuration

### Environment Variables (`.env`)

Edit the `.env` file in the project root to configure credentials and settings:

```env
FLASK_SECRET_KEY=change-this-to-a-random-secret-key
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=admin123
NGROK_AUTH_TOKEN=your-ngrok-token-here
FLASK_PORT=5000
```

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_SECRET_KEY` | Secret key for Flask session encryption. Change this to a random string. | `change-this-to-a-random-secret-key` |
| `DASHBOARD_USERNAME` | Username for dashboard login | `admin` |
| `DASHBOARD_PASSWORD` | Password for dashboard login | `admin123` |
| `NGROK_AUTH_TOKEN` | Your ngrok authentication token (get one at [ngrok.com](https://ngrok.com)) | `your-ngrok-token-here` |
| `FLASK_PORT` | Port for the web dashboard | `5000` |

> **Important:** Change the default username and password before using in production. For `FLASK_SECRET_KEY`, use a long random string.

### Task Configuration (`config/schedule.json`)

This file defines the tasks to automate, the schedule, and randomization rules. The default configuration includes 8 pre-configured tasks:

```json
{
  "tasks": [
    {
      "app": "insta",
      "module": "enviar_mensagem_direct",
      "duration_min": 45,
      "targeting": "local",
      "enabled": true
    },
    {
      "app": "face",
      "module": "entrar_em_grupos",
      "duration_min": 30,
      "targeting": "local",
      "enabled": true
    }
  ]
}
```

**Task fields:**

| Field | Description | Values |
|-------|-------------|--------|
| `app` | Target application | `"face"` or `"insta"` |
| `module` | Function/module name in Housoft to execute | String (e.g., `"entrar_em_grupos"`) |
| `duration_min` | Base execution duration in minutes | Number |
| `targeting` | Geographic targeting scope | `"local"` or `"national"` |
| `enabled` | Whether the task is active | `true` or `false` |

**Pre-configured tasks:**

| # | App | Module | Duration | Targeting |
|---|-----|--------|----------|-----------|
| 1 | Instagram | Send Direct Messages | 45 min | Local |
| 2 | Facebook | Enter Groups | 30 min | Local |
| 3 | Facebook | Post in Groups | 40 min | National |
| 4 | Facebook | Post on Wall | 30 min | Local |
| 5 | Facebook | Post Birthday Messages | 20 min | Local |
| 6 | Facebook | Send Messages | 35 min | Local |
| 7 | Facebook | Like Pages | 20 min | National |
| 8 | Facebook | Comment on Posts | 25 min | Local |

---

## Starting the Application

### 1. Make sure Housoft applications are running

Open Housoft Face and/or Housoft Instagram before starting the automation.

### 2. Activate the virtual environment

```bash
cd housoft-meta
venv\Scripts\activate
```

### 3. Run the application

```bash
python main.py
```

On startup, the console will display:

```
[INFO] GUI Engine initialized
[INFO] Task Orchestrator initialized
[INFO] ngrok tunnel established: https://xxxx-xx-xx.ngrok-free.app
[INFO] Dashboard available at:
[INFO]   Local:  http://localhost:5000
[INFO]   Mobile: https://xxxx-xx-xx.ngrok-free.app
```

### 4. Open the dashboard

- **Local access:** Open `http://localhost:5000` in your browser
- **Remote/Mobile access:** Use the ngrok URL displayed in the console

---

## Web Dashboard

### Login

Navigate to the dashboard URL. You will be redirected to the login page.

- **Username:** `admin` (or your configured value)
- **Password:** `admin123` (or your configured value)

### Dashboard Overview

After logging in, you will see the main dashboard with the following sections:

#### Status Card

Displays real-time system status:

- **Status Indicator:** Color-coded dot
  - Green/Teal = Running
  - Orange = Paused
  - Red = Stopped
- **Current Task:** Shows the currently executing app/module (or "None")
- **Intensity Mode:** Current time-based mode (Peak / Moderate / Off)
- **Active Tasks:** Number of enabled tasks

The status auto-refreshes every **5 seconds**.

#### Control Buttons

Four action buttons to control the orchestrator:

| Button | Action | Description |
|--------|--------|-------------|
| **Start** | Starts automation | Begins the task execution loop in a background thread |
| **Stop** | Stops automation | Stops the current task and halts the orchestrator |
| **Pause** | Pauses automation | Pauses the loop; the current task finishes naturally |
| **Resume** | Resumes automation | Continues from where it was paused |

#### Task List

Shows all configured tasks with:

- Module name
- App name (face/insta)
- Duration
- Targeting (local/national)
- **ON/OFF toggle** button to enable or disable each task

The task list refreshes every **15 seconds**.

#### Task History

Displays the most recent 10 completed tasks with:

- Status badge (Completed / Failed / Running)
- App and module name
- Planned duration
- Execution timestamp

### Logout

Click the **Logout** link in the header to end your session.

---

## Task Management

### Enabling/Disabling Tasks

From the dashboard, click the toggle button next to any task to enable or disable it. Disabled tasks are skipped during automation.

### How Tasks Execute

1. The orchestrator builds a queue from all **enabled** tasks
2. Task order is **shuffled randomly** (if randomization is enabled)
3. For each task:
   - The corresponding Housoft application window is brought to the foreground
   - The module is selected via image recognition (template matching)
   - The OK button is clicked to start the module
   - The task runs for its calculated duration
   - The "Parar" (Stop) button is clicked
   - A random delay (3-10 minutes) occurs before the next task
4. After all tasks complete, the cycle repeats

### Task Duration Calculation

The actual duration of each task is calculated as:

```
actual_duration = base_duration * (1 ± variation) * intensity_multiplier
```

- **base_duration:** The `duration_min` value from configuration
- **variation:** Random ±20% by default
- **intensity_multiplier:** Based on current time period (1.0 / 0.6 / 0.0)

**Example:** A 30-minute task during moderate hours:
- Base: 30 min
- With ±20% variation: 24-36 min
- With 0.6 intensity: 14.4-21.6 min

---

## Scheduling & Intensity

The system uses time-based intensity to simulate natural human behavior patterns.

### Time Periods

| Period | Hours | Intensity | Behavior |
|--------|-------|-----------|----------|
| **Peak** | 08:00-12:00, 14:00-18:00 | 100% | Full task execution |
| **Moderate** | 12:00-14:00, 18:00-22:00 | 60% | Reduced duration tasks |
| **Off** | 22:00-08:00 | 0% | No activity (system sleeps) |

### How Intensity Works

- During **Peak** hours, tasks run at their full configured duration
- During **Moderate** hours, task durations are multiplied by 0.6 (60%)
- During **Off** hours, the orchestrator sleeps and checks every 5 minutes until a non-off period begins

### Randomization Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Delay between tasks | 3-10 minutes | Random pause between task switches |
| Shuffle order | Enabled | Tasks execute in random order each cycle |
| Duration variation | ±20% | Random variation applied to task duration |

### Customizing the Schedule

Edit `config/schedule.json` directly, or use the API endpoint `POST /api/schedule` to update the configuration without restarting.

---

## Remote Access (Mobile)

The application uses **ngrok** to create a secure tunnel for remote access from your phone or any device.

### Setup

1. Create a free account at [ngrok.com](https://ngrok.com)
2. Copy your authentication token from the ngrok dashboard
3. Paste it in the `.env` file:
   ```
   NGROK_AUTH_TOKEN=your-actual-token-here
   ```
4. Restart the application

### Accessing from Mobile

1. Start the application on your computer
2. Note the ngrok URL shown in the console output
3. Open the URL on your phone's browser
4. Log in with your dashboard credentials
5. You can now monitor and control automation from your phone

> **Note:** The ngrok URL changes each time you restart the application (on the free plan). Consider upgrading to a paid ngrok plan for a fixed URL.

---

## API Reference

All API endpoints require authentication (active session). Send requests with the session cookie obtained after login.

### Status Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/status` | Returns current system status, intensity mode, and recent history |
| `GET` | `/api/history` | Returns the last 20 task history entries |

**Example response for `/api/status`:**
```json
{
  "is_running": true,
  "is_paused": false,
  "current_task": "entrar_em_grupos",
  "intensity_mode": "peak",
  "intensity_multiplier": 1.0,
  "task_history": [...],
  "enabled_tasks_count": 6
}
```

### Control Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/start` | Start the orchestrator |
| `POST` | `/api/stop` | Stop the orchestrator |
| `POST` | `/api/pause` | Pause the orchestrator |
| `POST` | `/api/resume` | Resume the orchestrator |

### Configuration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/schedule` | Get the full schedule configuration |
| `POST` | `/api/schedule` | Update the schedule configuration |
| `GET` | `/api/tasks` | Get all tasks |
| `POST` | `/api/tasks/<index>/toggle` | Toggle a task on/off by its index (0-based) |

---

## Safety Features

Housoft Meta includes several safety mechanisms:

### Emergency Stop

Move your mouse cursor to the **top-left corner** of the screen to trigger PyAutoGUI's failsafe and immediately abort all automation.

### Human-Like Behavior

- **Random delays:** 0.5s pause between all GUI actions
- **Click offset:** Random ±3 pixel offset on every click
- **Task delays:** 3-10 minute random gaps between tasks
- **Duration variation:** ±20% randomization on task durations
- **Shuffled order:** Tasks execute in random order each cycle

### Popup Handling

The system automatically detects and dismisses error or alert popups that may appear in Housoft applications during automation. The check runs every 30 seconds while a task is active.

### Graceful Shutdown

- **Pause** allows the current task to finish before halting the loop
- **Stop** cleanly terminates the background thread
- Task history is preserved after stopping

### Logging

All actions are logged to:
- **Console:** Real-time output
- **File:** `logs/housoft_meta.log`

Check the log file for debugging or reviewing automation history.

---

## Troubleshooting

### Application won't start

- Ensure Python 3.8+ is installed: `python --version`
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that the `.env` file exists and is properly configured

### Tasks are not executing

- Verify Housoft applications are **open and visible** on screen
- Ensure the application windows are not minimized
- Check that the current time is within **Peak** or **Moderate** hours
- Verify tasks are **enabled** in the dashboard
- Check `logs/housoft_meta.log` for error messages

### Image recognition fails (clicks miss)

- Ensure UI template images in the `templates/` folder match the current Housoft UI
- Adjust screen resolution to match when templates were captured
- Use `gui_engine.capture_template(name)` to re-capture templates for your screen

### Cannot access dashboard

- Check the Flask port is not in use by another application
- Try accessing `http://127.0.0.1:5000` instead of `localhost`
- Verify firewall is not blocking port 5000

### ngrok not working

- Verify your `NGROK_AUTH_TOKEN` is correct in `.env`
- Check your internet connection
- The free ngrok plan has connection limits; consider upgrading if needed
- The application will still work locally even if ngrok fails

### Dashboard shows "Stopped" but tasks should be running

- Click **Start** on the dashboard to begin the orchestrator
- The orchestrator does not auto-start; it must be started manually via the dashboard

---

## Project Structure

```
housoft-meta/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables & credentials
├── .gitignore                       # Git exclusions
├── generate_favicon.py              # Dashboard favicon generator
│
├── config/
│   └── schedule.json                # Task & schedule configuration
│
├── core/
│   ├── __init__.py
│   ├── gui_engine.py                # GUI automation engine (image recognition, clicking)
│   └── window_manager.py            # Window finding and focusing
│
├── orchestrator/
│   ├── __init__.py
│   └── scheduler.py                 # Task orchestrator, scheduling, intensity control
│
├── web/
│   ├── __init__.py
│   ├── app.py                       # Flask web server & REST API
│   ├── static/
│   │   ├── favicon.ico
│   │   └── favicon.png
│   └── templates/
│       ├── login.html               # Login page
│       └── dashboard.html           # Main dashboard
│
├── templates/                       # UI element screenshots for image recognition
└── logs/
    └── housoft_meta.log             # Application log file
```

---

## Quick Start Summary

1. Install dependencies: `pip install -r requirements.txt`
2. Edit `.env` with your credentials and ngrok token
3. Open Housoft Face and/or Instagram
4. Run: `python main.py`
5. Open `http://localhost:5000` in your browser
6. Log in with `admin` / `admin123`
7. Click **Start** to begin automation
8. Monitor tasks and toggle them on/off from the dashboard
