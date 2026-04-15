"""
Extract UI button templates from Housoft video frames at 1024x768 resolution.

Layout confirmed from marked inspection:
  y=0-20   : Housoft title bar
  y=20-30  : Bandicam watermark (center only - ignore)
  y=30-80  : Menu row 1 (text y=30-45, icon y=50-75)
  y=80-115 : Menu row 2 (text y=80-95, icon y=95-115)
"""
import cv2
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\Administrator\Documents\20260330_Automation and Scheduling of Functions in an Existing Program")
FRAMES_DIR = PROJECT_ROOT / "video" / "frames"
TEMPLATES_DIR = PROJECT_ROOT / "housoft-meta" / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

MAIN_FRAME = "bandicam_2026-04-09_17-44-06-253/frame_100_t0293.3s.jpg"

EXTRACTIONS = [
    # ─── Menu Row 1 (y=30-78): text + icon ───
    ("module_postar_em_grupos",   MAIN_FRAME, (5, 30, 100, 78)),
    ("module_postar_no_mural",    MAIN_FRAME, (100, 30, 195, 78)),
    ("module_enviar_mensagem",    MAIN_FRAME, (195, 30, 280, 78)),
    ("module_adicionar_amigos",   MAIN_FRAME, (280, 30, 375, 78)),
    ("module_paginas_eventos",    MAIN_FRAME, (375, 30, 465, 78)),
    ("module_login_loop",         MAIN_FRAME, (465, 30, 550, 78)),

    # ─── Menu Row 2 (y=78-115): text + icon ───
    ("module_postar_marketplace", MAIN_FRAME, (5, 78, 110, 115)),
    ("module_entrar_em_grupos",   MAIN_FRAME, (110, 78, 200, 115)),
    ("module_responder_mensagem", MAIN_FRAME, (200, 78, 300, 115)),
    ("module_curtir",             MAIN_FRAME, (300, 78, 380, 115)),
    ("module_compartilhar",       MAIN_FRAME, (380, 78, 470, 115)),
    ("module_criar_lista",        MAIN_FRAME, (470, 78, 555, 115)),

    # ─── Text-only variants (more reliable for matching; text y=30-45 and y=80-95) ───
    ("text_postar_em_grupos",   MAIN_FRAME, (5, 30, 100, 48)),
    ("text_postar_no_mural",    MAIN_FRAME, (100, 30, 195, 48)),
    ("text_enviar_mensagem",    MAIN_FRAME, (195, 30, 280, 48)),
    ("text_adicionar_amigos",   MAIN_FRAME, (280, 30, 375, 48)),
    ("text_paginas_eventos",    MAIN_FRAME, (375, 30, 465, 48)),
    ("text_login_loop",         MAIN_FRAME, (465, 30, 550, 48)),
    ("text_postar_marketplace", MAIN_FRAME, (5, 78, 110, 95)),
    ("text_entrar_em_grupos",   MAIN_FRAME, (110, 78, 200, 95)),
    ("text_responder_mensagem", MAIN_FRAME, (200, 78, 300, 95)),
    ("text_curtir",             MAIN_FRAME, (300, 78, 380, 95)),
    ("text_compartilhar",       MAIN_FRAME, (380, 78, 470, 95)),
    ("text_criar_lista",        MAIN_FRAME, (470, 78, 555, 95)),

    # ─── Titlebar (for window detection) ───
    ("titlebar_face", MAIN_FRAME, (4, 2, 310, 18)),

    # ─── Configurar button ───
    ("module_configurar", MAIN_FRAME, (558, 30, 650, 95)),
]


def extract():
    ok, fail = 0, 0
    for name, frame_path, (x1, y1, x2, y2) in EXTRACTIONS:
        src = FRAMES_DIR / frame_path
        if not src.exists():
            fail += 1
            continue
        img = cv2.imread(str(src))
        if img is None:
            fail += 1
            continue
        crop = img[y1:y2, x1:x2]
        out_path = TEMPLATES_DIR / f"{name}.png"
        cv2.imwrite(str(out_path), crop)
        print(f"[OK] {name}.png ({x2-x1}x{y2-y1})")
        ok += 1

    print(f"\nExtracted: {ok} | Failed: {fail}")


if __name__ == "__main__":
    extract()
