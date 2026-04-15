"""
Test OpenCV template matching against real Housoft frames from client videos.
This proves our templates can find UI elements in real Housoft screenshots.
"""
import cv2
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FRAMES_DIR = PROJECT_ROOT.parent / "video" / "frames"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Frames to test against (each covers different modules / dialog states)
TEST_FRAMES = [
    "bandicam_2026-04-09_17-44-06-253/frame_100_t0293.3s.jpg",  # main view
    "bandicam_2026-04-09_17-44-06-253/frame_020_t0058.7s.jpg",  # postar em grupos dialog
    "bandicam_2026-04-09_17-44-06-253/frame_150_t0440.0s.jpg",  # postar no mural
    "bandicam_2026-04-09_17-44-06-253/frame_200_t0586.7s.jpg",  # enviar mensagem
    "bandicam_2026-04-09_18-07-59-249/frame_030_t0088.5s.jpg",  # paginas eventos (task running)
    "bandicam_2026-04-09_18-12-25-520/frame_030_t0089.6s.jpg",  # postar marketplace
    "bandicam_2026-04-09_18-15-47-751/frame_050_t0145.5s.jpg",  # responder mensagem (task running)
]

# All module templates we care about
MODULE_TEMPLATES = [
    "module_postar_em_grupos",
    "module_postar_no_mural",
    "module_enviar_mensagem",
    "module_adicionar_amigos",
    "module_paginas_eventos",
    "module_login_loop",
    "module_postar_marketplace",
    "module_entrar_em_grupos",
    "module_responder_mensagem",
    "module_curtir",
    "module_compartilhar",
    "module_criar_lista",
    "module_configurar",
    "titlebar_face",
]


def find_template(screenshot, template, threshold=0.7):
    """Find a template in a screenshot. Returns (x, y, confidence) or None."""
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return (center_x, center_y, max_val)
    return None


def test_frame(frame_path):
    """Test all templates against one frame."""
    print(f"\n{'=' * 70}")
    print(f"Testing: {frame_path.name}")
    print(f"{'=' * 70}")

    img = cv2.imread(str(frame_path))
    if img is None:
        print(f"ERROR: Could not load frame")
        return {"found": 0, "total": 0}

    found = 0
    total = 0

    for tmpl_name in MODULE_TEMPLATES:
        tmpl_path = TEMPLATES_DIR / f"{tmpl_name}.png"
        if not tmpl_path.exists():
            continue

        template = cv2.imread(str(tmpl_path))
        if template is None:
            continue

        total += 1
        result = find_template(img, template, threshold=0.7)

        if result:
            x, y, conf = result
            status = "FOUND"
            found += 1
            print(f"  [OK]   {tmpl_name:30s} at ({x:4d}, {y:4d}) confidence={conf:.2f}")
        else:
            # Try with lower threshold to show best match
            best = find_template(img, template, threshold=0.0)
            if best:
                _, _, conf = best
                print(f"  [MISS] {tmpl_name:30s} best confidence={conf:.2f}")

    print(f"\n  Result: {found}/{total} templates found in this frame")
    return {"found": found, "total": total}


def main():
    if not TEMPLATES_DIR.exists():
        print(f"ERROR: Templates directory not found: {TEMPLATES_DIR}")
        return

    total_found = 0
    total_tested = 0

    for frame_rel in TEST_FRAMES:
        frame_path = FRAMES_DIR / frame_rel
        if not frame_path.exists():
            print(f"SKIP: Frame not found: {frame_rel}")
            continue

        result = test_frame(frame_path)
        total_found += result["found"]
        total_tested += result["total"]

    print(f"\n{'=' * 70}")
    print(f"OVERALL: {total_found}/{total_tested} templates matched across all frames")
    print(f"Success rate: {100 * total_found / total_tested:.1f}%")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
