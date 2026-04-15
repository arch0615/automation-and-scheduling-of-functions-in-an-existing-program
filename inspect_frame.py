"""Inspect regions of a frame by saving zoomed crops for review."""
import cv2
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\Administrator\Documents\20260330_Automation and Scheduling of Functions in an Existing Program")
FRAMES_DIR = PROJECT_ROOT / "video" / "frames"
OUT_DIR = PROJECT_ROOT / "housoft-meta" / "templates" / "_inspect"
OUT_DIR.mkdir(exist_ok=True, parents=True)

# Load the main view frame
frame_path = FRAMES_DIR / "bandicam_2026-04-09_17-44-06-253" / "frame_100_t0293.3s.jpg"
img = cv2.imread(str(frame_path))
h, w = img.shape[:2]
print(f"Frame size: {w}x{h}")

# Save stripe regions to identify exact button locations
regions = {
    "strip_top_00-20": (0, 0, w, 20),        # Housoft titlebar
    "strip_top_20-40": (0, 20, w, 40),       # Bandicam watermark area
    "strip_top_40-60": (0, 40, w, 60),       # First menu row?
    "strip_top_60-80": (0, 60, w, 80),       # Second menu row?
    "strip_top_80-100": (0, 80, w, 100),     # Sub-tabs?
    "strip_top_100-120": (0, 100, w, 120),
    "strip_top_0-100": (0, 0, w, 100),       # Full top region at 2x zoom
    "strip_top_0-120": (0, 0, w, 120),
}

for name, (x1, y1, x2, y2) in regions.items():
    crop = img[y1:y2, x1:x2]
    # Save at 2x zoom for easier inspection
    zoomed = cv2.resize(crop, (crop.shape[1]*2, crop.shape[0]*2), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(str(OUT_DIR / f"{name}.png"), zoomed)

# Also inspect the dialog frame for button positions
dialog_frame = FRAMES_DIR / "bandicam_2026-04-09_17-44-06-253" / "frame_020_t0058.7s.jpg"
dimg = cv2.imread(str(dialog_frame))

# Dialog frame - the dialog is visible. Save the whole left-center portion
cv2.imwrite(str(OUT_DIR / "dialog_full_left.png"), dimg[:, :500])

# And the bottom of the dialog area (find Ok/Ajuda/Cancelar)
cv2.imwrite(str(OUT_DIR / "dialog_bottom_y300-400.png"), dimg[300:400, :400])
cv2.imwrite(str(OUT_DIR / "dialog_bottom_y400-500.png"), dimg[400:500, :400])
cv2.imwrite(str(OUT_DIR / "dialog_bottom_y500-600.png"), dimg[500:600, :400])

print(f"Inspection images saved to: {OUT_DIR}")
