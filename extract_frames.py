"""
Extract frames from Housoft screen recordings for analysis.
Saves 1 frame every 3 seconds from each video.
"""
import cv2
import os
from pathlib import Path

VIDEO_DIR = Path(r"c:\Users\Administrator\Documents\20260330_Automation and Scheduling of Functions in an Existing Program\video")
OUTPUT_DIR = Path(r"c:\Users\Administrator\Documents\20260330_Automation and Scheduling of Functions in an Existing Program\video\frames")
OUTPUT_DIR.mkdir(exist_ok=True)

FRAME_INTERVAL_SEC = 3  # Extract one frame every N seconds

for video_file in sorted(VIDEO_DIR.glob("*.mp4")):
    print(f"\nProcessing: {video_file.name}")
    cap = cv2.VideoCapture(str(video_file))

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps if fps > 0 else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"  Duration: {duration_sec:.1f}s, FPS: {fps:.1f}, Resolution: {width}x{height}")

    # Create a subfolder for this video
    video_name = video_file.stem.replace(" ", "_")
    out_folder = OUTPUT_DIR / video_name
    out_folder.mkdir(exist_ok=True)

    frame_interval = int(fps * FRAME_INTERVAL_SEC) if fps > 0 else 90
    frame_num = 0
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num % frame_interval == 0:
            timestamp_sec = frame_num / fps if fps > 0 else 0
            out_path = out_folder / f"frame_{saved:03d}_t{timestamp_sec:06.1f}s.jpg"
            cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            saved += 1

        frame_num += 1

    cap.release()
    print(f"  Saved {saved} frames to {out_folder.name}/")

print(f"\nDone. Frames saved to {OUTPUT_DIR}")
