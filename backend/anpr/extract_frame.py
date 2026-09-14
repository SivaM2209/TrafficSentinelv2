from pathlib import Path
import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

VIDEO_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw_videos"
    / "trafficvideo.mp4"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "anpr_test"
    / "test_frame.jpg"
)

print("Video:", VIDEO_PATH)
print("Output:", OUTPUT_PATH)

cap = cv2.VideoCapture(str(VIDEO_PATH))

if not cap.isOpened():
    raise RuntimeError("Could not open traffic video.")

total_frames = int(
    cap.get(cv2.CAP_PROP_FRAME_COUNT)
)

print("Total frames:", total_frames)

# Go roughly to the middle of the video
middle_frame = total_frames // 2

cap.set(
    cv2.CAP_PROP_POS_FRAMES,
    middle_frame
)

success, frame = cap.read()

cap.release()

if not success:
    raise RuntimeError("Could not read frame.")

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

cv2.imwrite(
    str(OUTPUT_PATH),
    frame
)

print()
print("Frame extracted successfully!")
print(OUTPUT_PATH)