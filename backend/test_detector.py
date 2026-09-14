from services.detection.detector import VehicleDetector

detector = VehicleDetector(
    model_path="models/yolo11n.pt",
    confidence=0.40
)

results = detector.detect_video("../data/raw_videos/trafficvideo.mp4")

print(results)