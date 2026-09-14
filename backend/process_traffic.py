from services.tracking.tracker import VehicleTracker
from database.database import get_connection


VIDEO_PATH = "../data/raw_videos/trafficvideo.mp4"
MODEL_PATH = "../models/yolo11n.pt"
CAMERA_ID = "Camera01"


def clear_old_data():
    """Remove old demo/test vehicle records."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM vehicles")

    connection.commit()
    connection.close()

    print("Old vehicle data cleared.")


def save_unique_vehicles(results):
    """
    Save each unique tracked vehicle only once.
    """

    vehicles = {}

    for frame_data in results:

        frame_number = frame_data["frame"]

        for vehicle in frame_data["vehicles"]:

            track_id = vehicle["track_id"]

            # Ignore detections without a tracking ID
            if track_id is None:
                continue

            # Only keep the first occurrence of each vehicle
            if track_id not in vehicles:
                vehicles[track_id] = {
                    "vehicle_id": f"V-{track_id:04d}",
                    "vehicle_type": vehicle["vehicle_type"],
                    "camera_id": CAMERA_ID,
                    "timestamp": f"Frame {frame_number}"
                }

    connection = get_connection()
    cursor = connection.cursor()

    for vehicle in vehicles.values():

        cursor.execute("""
            INSERT INTO vehicles (
                vehicle_id,
                vehicle_type,
                camera_id,
                timestamp
            )
            VALUES (?, ?, ?, ?)
        """, (
            vehicle["vehicle_id"],
            vehicle["vehicle_type"],
            vehicle["camera_id"],
            vehicle["timestamp"]
        ))

    connection.commit()
    connection.close()

    return vehicles


def main():

    print("========================================")
    print("      TrafficSentinel Processor")
    print("========================================")
    print()

    print("Loading YOLO11 + ByteTrack...")

    tracker = VehicleTracker(
        model_path=MODEL_PATH,
        confidence=0.40
    )

    print("Model loaded.")
    print()

    print("Processing traffic video...")
    print("Video:", VIDEO_PATH)
    print()

    results = tracker.track_video(VIDEO_PATH)

    print()
    print("Video processing completed.")
    print("Total frames:", len(results))

    clear_old_data()

    print("Saving unique vehicles to database...")

    vehicles = save_unique_vehicles(results)

    print()
    print("========================================")
    print("Database update completed!")
    print("========================================")
    print()
    print("Unique vehicles saved:", len(vehicles))
    print()

    for vehicle in vehicles.values():
        print(
            vehicle["vehicle_id"],
            "|",
            vehicle["vehicle_type"],
            "|",
            vehicle["camera_id"],
            "|",
            vehicle["timestamp"]
        )


if __name__ == "__main__":
    main()