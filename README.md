# Housoft Meta-Automation System

A meta-automation layer that controls the Housoft desktop application to run Facebook and Instagram tasks 24/7 without manual intervention.

## Features

- **Automatic task switching** across 13 Facebook + Instagram modules
- **Smart scheduling** with peak / moderate / off-hours intensity control
- **Randomization** to avoid Meta's bot detection
- **Mobile-friendly web dashboard** (accessible via phone)
- **Category-based task ordering** (maintenance -> growth -> posting -> messaging -> engagement)
- **Login Loop safeguards** (never interrupted mid-cycle)
- **Watchdog supervisor** (auto-restart on crash)
- **Auto-start on Windows logon**

## Quick Start

```bash
# 1. Install
setup.bat

# 2. Configure (edit .env)
#    - Set DASHBOARD_PASSWORD
#    - Set NGROK_AUTH_TOKEN

# 3. Capture Housoft UI templates (one-time, on target machine)
py capture_templates.py

# 4. Start
start.bat
```

## Architecture

```
main.py
  |
  +-- core/gui_engine.py        GUI automation (pyautogui + OpenCV)
  |   core/window_manager.py    Find/focus Housoft windows
  |   core/click_sequences.py   Click paths for all 13 modules
  |   core/mock_gui_engine.py   Mock for testing without Housoft
  |
  +-- orchestrator/scheduler.py Task queue, randomization, intensity
  |
  +-- web/app.py                Flask dashboard + API
      web/templates/            HTML (login, dashboard, schedule editor)
      web/static/               favicon etc.
```

## Dashboard URLs

After starting:
- **Local**: http://localhost:5000
- **Mobile**: https://[your-ngrok].ngrok-free.app (auto-generated)

## Testing

Run end-to-end tests without needing Housoft:

```bash
py tests/test_orchestrator_e2e.py      # Orchestrator + Mock GUI (4 tests)
py tests/test_template_matching.py     # OpenCV template validation
```

## Documentation

- `docs/HOUSOFT_UI_MAP.md` - Housoft UI layout and click sequences
- `config/schedule.json` - Task schedule and settings
