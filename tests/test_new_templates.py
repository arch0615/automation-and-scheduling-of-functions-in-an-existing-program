"""
Validate the templates extracted from the 2026-04-24 client materials.
Each template is matched against the source it was extracted from to confirm
the crop is clean and confidence is high.
"""
import cv2
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
SOURCE_DIR = PROJECT_ROOT.parent / "0424"

# Each entry: (template_name, source_image_relative_path, label)
TESTS = [
    ("btn_parar",     "frames/frame_062_t0060.4s.png",      "running-state toolbar"),
    ("btn_pausa",     "frames/frame_062_t0060.4s.png",      "running-state toolbar"),
    ("btn_continuar", "frames/frame_185_t0180.3s.png",      "paused-state toolbar"),
    ("btn_ok",        "photo_2026-04-24_13-19-18.jpg",      "Postar em grupos dialog"),
    ("btn_ajuda",     "photo_2026-04-24_13-19-18.jpg",      "Postar em grupos dialog"),
    ("btn_cancelar",  "photo_2026-04-24_13-19-18.jpg",      "Postar em grupos dialog"),
    ("tab_conteudo",  "photo_2026-04-24_13-19-18.jpg",      "dialog top tabs"),
    ("tab_opcoes",    "photo_2026-04-24_13-19-18.jpg",      "dialog top tabs"),
    ("tab_filtros",   "photo_2026-04-24_13-19-18.jpg",      "dialog top tabs"),
    ("tab_criterio",  "photo_2026-04-24_13-19-18.jpg",      "Critério dropdown"),
]

THRESHOLD = 0.85  # high bar for self-match


def run():
    passed = failed = 0
    print(f"{'Template':<22}{'Confidence':<14}Status")
    print("-" * 70)
    for tmpl_name, src_rel, label in TESTS:
        tmpl_path = TEMPLATES_DIR / f"{tmpl_name}.png"
        src_path = SOURCE_DIR / src_rel
        if not tmpl_path.exists():
            print(f"{tmpl_name:<22}{'-':<14}MISSING template file")
            failed += 1
            continue
        if not src_path.exists():
            print(f"{tmpl_name:<22}{'-':<14}MISSING source: {src_rel}")
            failed += 1
            continue
        screenshot = cv2.imread(str(src_path))
        template = cv2.imread(str(tmpl_path))
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        ok = max_val >= THRESHOLD
        status = "PASS" if ok else "FAIL"
        print(f"{tmpl_name:<22}{max_val:<14.3f}{status}  ({label})")
        if ok:
            passed += 1
        else:
            failed += 1
    print("-" * 70)
    print(f"Total: {passed} passed, {failed} failed")


if __name__ == "__main__":
    run()
