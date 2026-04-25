"""
Live Template Capture Tool

Run this on Valesca's machine (via AnyDesk) to capture pixel-perfect templates
of every Housoft button. The tool prompts you to hover the mouse over each
button, then captures a region around the cursor.

Usage:
    py capture_templates.py

Controls:
    - Position mouse over target button
    - Press ENTER to capture
    - Press 's' to skip current template
    - Press 'q' to quit
"""
import sys
import time
import cv2
import numpy as np
import pyautogui
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

# Default crop size around cursor (width, height)
DEFAULT_CROP_SIZE = (100, 40)
LARGE_CROP_SIZE = (120, 60)
TALL_CROP_SIZE = (100, 60)

# Templates to capture in order
CAPTURE_LIST = [
    # ═══ Essential - always capture these ═══
    ("titlebar_face",            "Hover over 'Housoft Face' title bar text",      (300, 20)),
    ("titlebar_insta",           "Hover over 'Housoft Insta' title bar text",     (300, 20)),

    # Menu buttons - row 1
    ("module_postar_em_grupos",  "Hover over 'Postar em grupos' button",          TALL_CROP_SIZE),
    ("module_postar_no_mural",   "Hover over 'Postar no mural' button",           TALL_CROP_SIZE),
    ("module_enviar_mensagem",   "Hover over 'Enviar mensagem' button",           TALL_CROP_SIZE),
    ("module_adicionar_amigos",  "Hover over 'Adicionar amigos' button",          TALL_CROP_SIZE),
    ("module_paginas_eventos",   "Hover over 'Paginas e eventos' button",         TALL_CROP_SIZE),
    ("module_login_loop",        "Hover over 'Login loop' button",                TALL_CROP_SIZE),

    # Menu buttons - row 2
    ("module_postar_marketplace","Hover over 'Postar no marketplace' button",     TALL_CROP_SIZE),
    ("module_entrar_em_grupos",  "Hover over 'Entrar em grupos' button",          TALL_CROP_SIZE),
    ("module_responder_mensagem","Hover over 'Responder mensagem' button",        TALL_CROP_SIZE),
    ("module_curtir",            "Hover over 'Curtir' button",                    TALL_CROP_SIZE),
    ("module_compartilhar",      "Hover over 'Compartilhar' button",              TALL_CROP_SIZE),
    ("module_criar_lista",       "Hover over 'Criar lista' button",               TALL_CROP_SIZE),

    # ═══ Dialog buttons (need a module dialog open) ═══
    ("btn_ok",                   "Open a module, then hover over the 'Ok' button", (70, 40)),
    ("btn_ajuda",                "Hover over the 'Ajuda' button",                  (70, 40)),
    ("btn_cancelar",             "Hover over the 'Cancelar' button",               (90, 40)),

    # Dialog tabs
    ("tab_criterio",             "Hover over 'Criterio' tab",                     (80, 25)),
    ("tab_conteudo",             "Hover over 'Conteudo' tab",                     (80, 25)),
    ("tab_opcoes",               "Hover over 'Opcoes' tab",                       (70, 25)),
    ("tab_filtros",              "Hover over 'Filtros' tab",                      (70, 25)),

    # ═══ Task control buttons (need a task running) ═══
    ("btn_parar",                "Start a task, then hover over the red 'Parar' button", (60, 40)),
    ("btn_pausa",                "Hover over the blue 'Pausa' button",            (60, 40)),
    ("btn_continuar",            "If task is paused, hover over blue 'Cont.' button", (60, 40)),

    # ═══ Instagram modules (need Housoft Insta open) ═══
    ("module_enviar_direct",     "Switch to Housoft Insta, hover over 'Enviar Direct'", TALL_CROP_SIZE),

    # ═══ Instagram Insta modules (may need separate documentation) ═══
    # Add more as they become known

    # ═══ Popups and errors (capture opportunistically) ═══
    ("popup_blocked",            "If an account-blocked popup appears, capture it",  (200, 100)),
    ("popup_error",              "If an error popup appears, capture it",            (200, 100)),
]


def capture_template(name, crop_size):
    """Capture a region around the current mouse position."""
    x, y = pyautogui.position()
    w, h = crop_size

    # Calculate crop bounds (centered on cursor)
    left = max(0, x - w // 2)
    top = max(0, y - h // 2)

    # Take the screenshot
    screenshot = pyautogui.screenshot(region=(left, top, w, h))
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Save
    out_path = TEMPLATES_DIR / f"{name}.png"
    cv2.imwrite(str(out_path), img)

    # Also save a preview with cursor marker for verification
    preview = img.copy()
    cv2.circle(preview, (w // 2, h // 2), 3, (0, 0, 255), -1)
    cv2.imwrite(str(TEMPLATES_DIR / f"_preview_{name}.png"), preview)

    return out_path


def wait_for_input():
    """Wait for ENTER, 's', or 'q' from stdin."""
    try:
        import msvcrt
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b"\r", b"\n"):
                    return "enter"
                elif key == b"s":
                    return "skip"
                elif key == b"q":
                    return "quit"
            time.sleep(0.05)
    except ImportError:
        # Fallback for non-Windows (shouldn't happen but just in case)
        ans = input("[ENTER/s/q]: ").strip().lower()
        if ans == "s":
            return "skip"
        if ans == "q":
            return "quit"
        return "enter"


def main():
    print("\n" + "=" * 70)
    print(" HOUSOFT TEMPLATE CAPTURE TOOL")
    print("=" * 70)
    print(f"\nThis tool will capture {len(CAPTURE_LIST)} templates for Housoft automation.")
    print(f"Templates will be saved to: {TEMPLATES_DIR}\n")
    print("Instructions:")
    print("  1. Make sure Housoft Face is open and visible")
    print("  2. For each prompt, hover your mouse over the button described")
    print("  3. Press ENTER to capture, 's' to skip, 'q' to quit")
    print("\nPress ENTER when ready to start...")
    wait_for_input()

    captured = 0
    skipped = 0

    for idx, (name, description, crop_size) in enumerate(CAPTURE_LIST, 1):
        # If crop_size is a 2-tuple of ints, use it. Otherwise use default.
        if not (isinstance(crop_size, tuple) and len(crop_size) == 2):
            crop_size = DEFAULT_CROP_SIZE

        print(f"\n[{idx}/{len(CAPTURE_LIST)}] Template: {name}")
        print(f"   Task: {description}")
        print(f"   Crop size: {crop_size[0]}x{crop_size[1]}")
        print(f"   Position mouse, then press ENTER (s=skip, q=quit)...")

        action = wait_for_input()
        if action == "quit":
            print("\nCapture aborted by user.")
            break
        if action == "skip":
            print(f"   [SKIPPED]")
            skipped += 1
            continue

        # Countdown so user sees where cursor is
        for i in range(3, 0, -1):
            x, y = pyautogui.position()
            print(f"   Capturing in {i}... (cursor at {x},{y})", end="\r")
            time.sleep(1)

        out_path = capture_template(name, crop_size)
        print(f"   [CAPTURED] -> {out_path.name}                    ")
        captured += 1

    print("\n" + "=" * 70)
    print(f" DONE: {captured} captured, {skipped} skipped, {len(CAPTURE_LIST) - captured - skipped} not processed")
    print(f" Templates saved to: {TEMPLATES_DIR}")
    print(f" Preview images with cursor marker: _preview_*.png")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
