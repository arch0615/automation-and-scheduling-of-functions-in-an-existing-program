"""
Inspect frames showing tasks RUNNING to find:
- Parar button position
- Pausa / Cont. button position
- Active task name region
- Status bar region
"""
import cv2
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\Administrator\Documents\20260330_Automation and Scheduling of Functions in an Existing Program")
FRAMES_DIR = PROJECT_ROOT / "video" / "frames"
OUT_DIR = PROJECT_ROOT / "housoft-meta" / "templates" / "_inspect"
OUT_DIR.mkdir(exist_ok=True, parents=True)


def mark_grid(img, step=20, color=(0, 255, 0), font_color=(0, 0, 255)):
    """Add x/y grid lines to an image for coordinate reading."""
    h, w = img.shape[:2]
    marked = img.copy()
    for x in range(0, w, step):
        cv2.line(marked, (x, 0), (x, h), color, 1)
        cv2.putText(marked, str(x), (x+2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.3, font_color, 1)
    for y in range(0, h, step):
        cv2.line(marked, (0, y), (w, y), color, 1)
        cv2.putText(marked, str(y), (2, y+10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, font_color, 1)
    return marked


# ─── 1024x768: Running state (bandicam_2026-04-17 frame_030) ───
img1 = cv2.imread(str(FRAMES_DIR / "bandicam_2026-04-17_11-45-42-629" / "frame_030_t0088.3s.jpg"))
print(f"Video 1 frame: {img1.shape[1]}x{img1.shape[0]}")

# Top toolbar area at 2x zoom
top1 = img1[0:120, 0:1024]
zoomed1 = cv2.resize(top1, (top1.shape[1]*2, top1.shape[0]*2), interpolation=cv2.INTER_NEAREST)
marked1 = mark_grid(zoomed1, step=20)
cv2.imwrite(str(OUT_DIR / "v1_top_marked.png"), marked1)

# Status bar area at 2x zoom
status1 = img1[700:768, 0:600]
zoomed_s1 = cv2.resize(status1, (status1.shape[1]*2, status1.shape[0]*2), interpolation=cv2.INTER_NEAREST)
marked_s1 = mark_grid(zoomed_s1, step=20)
cv2.imwrite(str(OUT_DIR / "v1_status_marked.png"), marked_s1)


# ─── 1280x720: Running state (Gravar frame_030) ───
img2 = cv2.imread(str(FRAMES_DIR / "Gravar_2026_04_17_12_54_21_636" / "frame_030_t0089.6s.jpg"))
print(f"Video 2 frame: {img2.shape[1]}x{img2.shape[0]}")

top2 = img2[0:120, 0:1280]
zoomed2 = cv2.resize(top2, (top2.shape[1]*2, top2.shape[0]*2), interpolation=cv2.INTER_NEAREST)
marked2 = mark_grid(zoomed2, step=20)
cv2.imwrite(str(OUT_DIR / "v2_top_marked.png"), marked2)


# ─── 1280x720: Paused state with Cont. button (Gravar frame_090) ───
img3 = cv2.imread(str(FRAMES_DIR / "Gravar_2026_04_17_12_54_21_636" / "frame_090_t0268.7s.jpg"))
print(f"Video 3 frame (paused): {img3.shape[1]}x{img3.shape[0]}")

top3 = img3[0:120, 0:1280]
zoomed3 = cv2.resize(top3, (top3.shape[1]*2, top3.shape[0]*2), interpolation=cv2.INTER_NEAREST)
marked3 = mark_grid(zoomed3, step=20)
cv2.imwrite(str(OUT_DIR / "v3_paused_marked.png"), marked3)


print(f"\nMarked images saved to: {OUT_DIR}")
print("Files: v1_top_marked, v1_status_marked, v2_top_marked, v3_paused_marked")
