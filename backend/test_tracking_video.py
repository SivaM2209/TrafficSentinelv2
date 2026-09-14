from services.tracking.tracker import VehicleTracker


VIDEO_PATH = "../data/raw_videos/trafficvideo.mp4"
MODEL_PATH = "../models/yolo11n.pt"


print("Loading YOLO11 model...")

tracker = VehicleTracker(
    model_path=MODEL_PATH,
    confidence=0.40
)

print("Starting vehicle tracking...")
print("Video:", VIDEO_PATH)
print()

results = tracker.track_video(VIDEO_PATH)

print("Tracking completed!")
print("Total frames processed:", len(results))

total_detections = 0
unique_vehicle_ids = set()

for frame in results:
    for vehicle in frame["vehicles"]:
        total_detections += 1

        if vehicle["track_id"] is not None:
            unique_vehicle_ids.add(vehicle["track_id"])

print("Total vehicle detections:", total_detections)
print("Unique tracked vehicles:", len(unique_vehicle_ids))

print()
print("First 5 frames:")

for frame in results[:5]:
    print(frame)
    