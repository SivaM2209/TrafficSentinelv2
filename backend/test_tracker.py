from services.tracking.tracker import VehicleTracker


VIDEO_PATH = "../data/raw_videos/trafficvideo.mp4"


tracker = VehicleTracker(
    model_path="models/yolo11n.pt",
    confidence=0.40
)


results = tracker.track_video(VIDEO_PATH)


for frame in results:

    print(f"\nFrame: {frame['frame']}")

    for vehicle in frame["vehicles"]:

        print(
            f"ID: {vehicle['track_id']} | "
            f"Type: {vehicle['vehicle_type']} | "
            f"Confidence: {vehicle['confidence']}"
        )