from pathlib import Path
import cv2
from ultralytics import YOLO


# --------------------------------------------------
# Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

VIDEO_PATH = PROJECT_ROOT / "data" / "raw_videos" / "trafficvideo.mp4"
MODEL_PATH = BACKEND_DIR / "models" / "yolo11n.pt"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed_videos" / "traffic_detected.mp4"


# --------------------------------------------------
# Vehicle classes
# --------------------------------------------------

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


# --------------------------------------------------
# Main processing
# --------------------------------------------------

def main():

    print("========================================")
    print("   TrafficSentinel Video Processor")
    print("========================================")
    print()

    # Check input files
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(
            f"Traffic video not found: {VIDEO_PATH}"
        )

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"YOLO model not found: {MODEL_PATH}"
        )

    print("Video:", VIDEO_PATH)
    print("Model:", MODEL_PATH)
    print()

    # Load YOLO model
    print("Loading YOLO11 model...")

    model = YOLO(str(MODEL_PATH))

    print("Model loaded.")
    print()

    # Open input video
    cap = cv2.VideoCapture(str(VIDEO_PATH))

    if not cap.isOpened():
        raise RuntimeError(
            "Could not open traffic video."
        )

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print("Video information:")
    print("  Width:", width)
    print("  Height:", height)
    print("  FPS:", fps)
    print("  Total frames:", total_frames)
    print()

    # Create output directory
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # MP4 video writer
    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        str(OUTPUT_PATH),
        fourcc,
        fps,
        (width, height)
    )

    if not writer.isOpened():
        raise RuntimeError(
            "Could not create output video."
        )

    print("Starting vehicle detection and tracking...")
    print()

    frame_number = 0
    unique_vehicle_ids = set()

    while True:

        success, frame = cap.read()

        if not success:
            break

        # YOLO tracking
        results = model.track(
            source=frame,
            conf=0.40,
            tracker="bytetrack.yaml",
            persist=True,
            verbose=False
        )

        result = results[0]

        # Draw detections
        if result.boxes is not None:

            for box in result.boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                # Ignore non-vehicle objects
                if class_id not in VEHICLE_CLASSES:
                    continue

                vehicle_type = VEHICLE_CLASSES[class_id]

                # Get tracking ID
                track_id = None

                if box.id is not None:
                    track_id = int(box.id[0])
                    unique_vehicle_ids.add(track_id)

                # Bounding box
                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )

                # Label
                if track_id is not None:
                    label = (
                        f"{vehicle_type.upper()} "
                        f"ID:{track_id} "
                        f"{confidence:.2f}"
                    )
                else:
                    label = (
                        f"{vehicle_type.upper()} "
                        f"{confidence:.2f}"
                    )

                # Draw bounding box
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                # Draw label background
                (text_width, text_height), baseline = (
                    cv2.getTextSize(
                        label,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        2
                    )
                )

                label_y = max(
                    y1,
                    text_height + baseline + 5
                )

                cv2.rectangle(
                    frame,
                    (x1, label_y - text_height - baseline - 5),
                    (x1 + text_width + 5, label_y),
                    (0, 255, 0),
                    -1
                )

                # Draw label
                cv2.putText(
                    frame,
                    label,
                    (x1 + 2, label_y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 0),
                    2
                )

        # Add frame information
        info = (
            f"Frame: {frame_number}/{total_frames}  "
            f"Tracked vehicles: {len(unique_vehicle_ids)}"
        )

        cv2.putText(
            frame,
            info,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # Write processed frame
        writer.write(frame)

        frame_number += 1

        # Progress
        if frame_number % 50 == 0:
            print(
                f"Processed {frame_number}/{total_frames} "
                f"frames..."
            )

    # Cleanup
    cap.release()
    writer.release()

    print()
    print("========================================")
    print("Processing completed!")
    print("========================================")
    print()
    print("Frames processed:", frame_number)
    print(
        "Unique vehicles detected:",
        len(unique_vehicle_ids)
    )
    print()
    print("Output video:")
    print(OUTPUT_PATH)
    print()


if __name__ == "__main__":
    main()