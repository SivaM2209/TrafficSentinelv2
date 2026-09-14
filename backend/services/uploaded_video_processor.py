from pathlib import Path
import json
import cv2
import subprocess

from ultralytics import YOLO

from database.database import get_connection

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
MODEL_PATH = BACKEND_DIR / "models" / "yolo11n.pt"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed_videos"

VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


def process_uploaded_video(camera_id: int, input_path: Path):
    if not input_path.exists():
        raise FileNotFoundError(f"Uploaded video not found: {input_path}")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"YOLO model not found: {MODEL_PATH}")

    camera_folder = PROCESSED_PATH / f"camera_{camera_id}"
    camera_folder.mkdir(parents=True, exist_ok=True)
    temporary_output = camera_folder / "processed_temp.mp4"
    final_output = camera_folder / "processed_video.mp4"
    summary_path = camera_folder / "analysis_summary.json"

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM vehicles WHERE camera_id = ?", (f"Camera{camera_id:02d}",))
    connection.commit()
    connection.close()

    model = YOLO(str(MODEL_PATH))
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError("Could not open uploaded video.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_area = max(1, width * height)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(temporary_output), fourcc, fps, (width, height))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError("Could not create temporary output video.")

    unique_vehicles = {}
    frame_vehicle_counts = []
    frame_occupancies = []
    confidence_values = []
    frame_number = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        results = model.track(source=frame, conf=0.40, tracker="bytetrack.yaml", persist=True, verbose=False)
        result = results[0]
        current_count = 0
        occupied_area = 0

        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                if class_id not in VEHICLE_CLASSES:
                    continue

                vehicle_type = VEHICLE_CLASSES[class_id]
                confidence_values.append(confidence)
                current_count += 1

                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                occupied_area += max(0, x2 - x1) * max(0, y2 - y1)
                track_id = int(box.id[0]) if box.id is not None else None

                if track_id is not None:
                    entry = unique_vehicles.setdefault(track_id, {
                        "vehicle_type": vehicle_type,
                        "first_frame": frame_number,
                        "last_frame": frame_number,
                        "frames_seen": 0,
                        "max_confidence": confidence,
                    })
                    entry["last_frame"] = frame_number
                    entry["frames_seen"] += 1
                    entry["max_confidence"] = max(entry["max_confidence"], confidence)

                label = f"{vehicle_type.upper()}" + (f" ID:{track_id}" if track_id is not None else "") + f" {confidence:.2f}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, max(25, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        frame_vehicle_counts.append(current_count)
        frame_occupancies.append(min(100.0, occupied_area / frame_area * 100.0))
        info = f"Camera {camera_id:02d} | Frame {frame_number}/{total_frames} | Vehicles {len(unique_vehicles)}"
        cv2.putText(frame, info, (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        writer.write(frame)
        frame_number += 1

    cap.release()
    writer.release()

    subprocess.run([
        "ffmpeg", "-y", "-i", str(temporary_output), "-c:v", "libx264", "-preset", "fast",
        "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", str(final_output)
    ], check=True)

    if temporary_output.exists():
        temporary_output.unlink()

    camera_name = f"Camera{camera_id:02d}"
    connection = get_connection()
    cursor = connection.cursor()
    for track_id, data in unique_vehicles.items():
        vehicle_id = f"C{camera_id:02d}-V-{track_id:04d}"
        cursor.execute("""
            INSERT INTO vehicles (vehicle_id, vehicle_type, camera_id, timestamp)
            VALUES (?, ?, ?, ?)
        """, (vehicle_id, data["vehicle_type"], camera_name, f"Frame {data['first_frame']}–{data['last_frame']}"))
    connection.commit()
    connection.close()

    unique_types = {name: 0 for name in VEHICLE_CLASSES.values()}
    for data in unique_vehicles.values():
        unique_types[data["vehicle_type"]] += 1

    summary = {
        "camera_id": camera_id,
        "total_unique_vehicles": len(unique_vehicles),
        "peak_vehicles_per_frame": max(frame_vehicle_counts, default=0),
        "average_vehicles_per_frame": round(sum(frame_vehicle_counts) / max(1, len(frame_vehicle_counts)), 2),
        "traffic_density": round(sum(frame_occupancies) / max(1, len(frame_occupancies)), 2),
        "average_confidence": round(sum(confidence_values) / max(1, len(confidence_values)), 3),
        "total_frames": frame_number,
        "fps": round(float(fps), 2),
        "duration_seconds": round(frame_number / max(float(fps), 1), 2),
        "vehicle_types": unique_types,
        "active_alerts": 0,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return final_output, summary
