"""Create fine-grained strips to find exact menu row positions."""
import cv2
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\Administrator\Documents\20260330_Automation and Scheduling of Functions in an Existing Program")
FRAMES_DIR = PROJECT_ROOT / "video" / "frames"
OUT_DIR = PROJECT_ROOT / "housoft-meta" / "templates" / "_inspect"
OUT_DIR.mkdir(exist_ok=True, parents=True)

frame_path = FRAMES_DIR / "bandicam_2026-04-09_17-44-06-253" / "frame_100_t0293.3s.jpg"
img = cv2.imread(str(frame_path))

# Extract y=0 to y=120 region at 3x zoom
top_region = img[0:120, 0:700]
zoomed = cv2.resize(top_region, (top_region.shape[1]*3, top_region.shape[0]*3), interpolation=cv2.INTER_NEAREST)
cv2.imwrite(str(OUT_DIR / "top_3x_zoomed.png"), zoomed)

# Also draw horizontal lines every 10px to help measurement
marked = top_region.copy()
for y in range(0, 120, 10):
    cv2.line(marked, (0, y), (700, y), (0, 255, 0), 1)
    cv2.putText(marked, str(y), (5, y+8), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)

zoomed_marked = cv2.resize(marked, (marked.shape[1]*3, marked.shape[0]*3), interpolation=cv2.INTER_NEAREST)
cv2.imwrite(str(OUT_DIR / "top_3x_marked.png"), zoomed_marked)

print("Saved top_3x_marked.png with y-coordinate grid lines")
