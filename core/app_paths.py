"""
Resolve user-data paths (.env, config, templates, logs).

When running from source: project root is `housoft-meta/`.
When frozen (PyInstaller .exe): user data lives next to the .exe so
Miguel/Valesca can edit `.env`, `config/schedule.json`, swap template
PNGs, and read `logs/` without unpacking the bundle.
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def env_path() -> Path:
    return app_dir() / ".env"


def config_dir() -> Path:
    d = app_dir() / "config"
    d.mkdir(parents=True, exist_ok=True)
    return d


def templates_dir() -> Path:
    return app_dir() / "templates"


def logs_dir() -> Path:
    d = app_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_env_file() -> None:
    """Load `.env` next to the exe, tolerating Windows-1252/UTF-16 saves.

    Notepad on Windows saves as ANSI (cp1252) by default; some users save
    as UTF-16. python-dotenv defaults to UTF-8 and crashes hard on a
    decode error. We try a few encodings and silently fall back.
    """
    path = env_path()
    if not path.exists():
        return
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            load_dotenv(path, encoding=enc)
            return
        except UnicodeDecodeError:
            continue
