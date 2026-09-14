from pathlib import Path
import cv2
import subprocess

from ultralytics import YOLO

from database.database import get_connection


# ==================================================
# PATHS
# ==================================================

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

MODEL_PATH = BACKEND_DIR / "models" / "yolo11n.pt"

UPLOAD_PATH = PROJECT_ROOT / "data" / "uploads"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed_videos"


# ==================================================
# VEHICLE CLASSES
# ==================================================

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


# ==================================================
# PROCESS UPLOADED VIDEO
# ==================================================

def process_uploaded_video(camera_id: int, input_path: Path):

    print()
    print("========================================")
    print(" TrafficSentinel Uploaded Video Processor")
    print("========================================")
    print()

    if not input_path.exists():
        raise FileNotFoundError(
            f"Uploaded video not found: {input_path}"
        )

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"YOLO model not found: {MODEL_PATH}"
        )

    # --------------------------------------------------
    # Output paths
    # --------------------------------------------------

    camera_processed_folder = (
        PROCESSED_PATH / f"camera_{camera_id}"
    )

    camera_processed_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_output = (
        camera_processed_folder / "processed_temp.mp4"
    )

    final_output = (
        camera_processed_folder / "processed_video.mp4"
    )

    # --------------------------------------------------
    # Clear old database records for this camera
    # --------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM vehicles WHERE camera_id = ?",
        (f"Camera{camera_id:02d}",)
    )

    connection.commit()
    connection.close()

    # --------------------------------------------------
    # Load YOLO
    # --------------------------------------------------

    print("Loading YOLO11 model...")

    model = YOLO(str(MODEL_PATH))

    print("Model loaded.")
    print()

    # --------------------------------------------------
    # Open video
    # --------------------------------------------------

    cap = cv2.VideoCapture(str(input_path))

    if not cap.isOpened():
        raise RuntimeError(
            "Could not open uploaded video."
        )

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 30

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    total_frames = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    print("Video information:")
    print(" Width:", width)
    print(" Height:", height)
    print(" FPS:", fps)
    print(" Total frames:", total_frames)
    print()

    # --------------------------------------------------
    # Temporary MP4 writer
    # --------------------------------------------------

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        str(temporary_output),
        fourcc,
        fps,
        (width, height)
    )

    if not writer.isOpened():
        cap.release()

        raise RuntimeError(
            "Could not create temporary output video."
        )

    # --------------------------------------------------
    # Tracking
    # --------------------------------------------------

    unique_vehicles = {}

    frame_number = 0

    print("Starting YOLO + ByteTrack processing...")
    print()

    while True:

        success, frame = cap.read()

        if not success:
            break

        results = model.track(
            source=frame,
            conf=0.40,
            tracker="bytetrack.yaml",
            persist=True,
            verbose=False
        )

        result = results[0]

        if result.boxes is not None:

            for box in result.boxes:

                class_id = int(
                    box.cls[0]
                )

                confidence = float(
                    box.conf[0]
                )

                if class_id not in VEHICLE_CLASSES:
                    continue

                vehicle_type = VEHICLE_CLASSES[
                    class_id
                ]

                track_id = None

                if box.id is not None:

                    track_id = int(
                        box.id[0]
                    )

                    unique_vehicles[
                        track_id
                    ] = vehicle_type

                # ------------------------------------------
                # Bounding box
                # ------------------------------------------

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )

                # ------------------------------------------
                # Vehicle label
                # ------------------------------------------

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

                # ------------------------------------------
                # Draw bounding box
                # ------------------------------------------

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                # ------------------------------------------
                # Label background
                # ------------------------------------------

                (
                    text_width,
                    text_height
                ), baseline = cv2.getTextSize(
                    label,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    2
                )

                label_y = max(
                    y1,
                    text_height + baseline + 5
                )

                cv2.rectangle(
                    frame,
                    (
                        x1,
                        label_y
                        - text_height
                        - baseline
                        - 5
                    ),
                    (
                        x1
                        + text_width
                        + 5,
                        label_y
                    ),
                    (0, 255, 0),
                    -1
                )

                # ------------------------------------------
                # Draw label
                # ------------------------------------------

                cv2.putText(
                    frame,
                    label,
                    (
                        x1 + 2,
                        label_y - 5
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 0),
                    2
                )

        # --------------------------------------------------
        # Frame information
        # --------------------------------------------------

        info = (
            f"Camera {camera_id:02d} | "
            f"Frame: {frame_number}/{total_frames} | "
            f"Vehicles: {len(unique_vehicles)}"
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

        # --------------------------------------------------
        # Write frame
        # --------------------------------------------------

        writer.write(frame)

        frame_number += 1

        if frame_number % 50 == 0:

            print(
                f"Processed "
                f"{frame_number}/{total_frames} "
                f"frames..."
            )

    cap.release()
    writer.release()

    print()
    print("YOLO + ByteTrack processing completed.")
    print(
        "Unique vehicles:",
        len(unique_vehicles)
    )
    print()

    # ==================================================
    # CONVERT TO H.264 FOR BROWSER
    # ==================================================

    print("Converting processed video to H.264...")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(temporary_output),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(final_output)
        ],
        check=True
    )

    # Remove temporary mp4v video

    if temporary_output.exists():
        temporary_output.unlink()

    print("Browser-compatible video created:")
    print(final_output)
    print()

    # ==================================================
    # SAVE VEHICLES TO DATABASE
    # ==================================================

    camera_name = f"Camera{camera_id:02d}"

    connection = get_connection()
    cursor = connection.cursor()

    for track_id, vehicle_type in unique_vehicles.items():

        vehicle_id = (
            f"C{camera_id:02d}-V-{track_id:04d}"
        )

        cursor.execute(
            """
            INSERT INTO vehicles (
                vehicle_id,
                vehicle_type,
                camera_id,
                timestamp
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                vehicle_id,
                vehicle_type,
                camera_name,
                f"Processed video"
            )
        )

    connection.commit()
    connection.close()

    print(
        f"Saved {len(unique_vehicles)} "
        f"vehicles to database."
    )

    print()

    return final_output