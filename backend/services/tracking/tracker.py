from pathlib import Path
from ultralytics import YOLO


class VehicleTracker:
    """
    TrafficSentinel vehicle tracker.

    Uses YOLO11 + ByteTrack to assign persistent IDs
    to vehicles across video frames.
    """

    VEHICLE_CLASSES = {
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck",
    }

    def __init__(
        self,
        model_path="models/yolo11n.pt",
        confidence=0.40,
        tracker="bytetrack.yaml"
    ):
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.tracker = tracker

    def track_video(self, video_path):
        """
        Track vehicles throughout a video.

        Returns:
            List of frame-by-frame tracking results.
        """

        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(
                f"Video not found: {video_path}"
            )

        results = self.model.track(
            source=str(video_path),
            conf=self.confidence,
            tracker=self.tracker,
            persist=True,
            stream=True,
            verbose=False
        )

        all_frames = []

        for frame_number, result in enumerate(results):

            frame_detections = []

            if result.boxes is None:
                all_frames.append({
                    "frame": frame_number,
                    "vehicles": []
                })
                continue

            for box in result.boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                # Ignore objects that aren't vehicles
                if class_id not in self.VEHICLE_CLASSES:
                    continue

                # Tracker ID
                track_id = None

                if box.id is not None:
                    track_id = int(box.id[0])

                # Bounding box
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                frame_detections.append({
                    "track_id": track_id,
                    "vehicle_type": self.VEHICLE_CLASSES[class_id],
                    "confidence": round(confidence, 3),
                    "bounding_box": {
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "x2": round(x2, 2),
                        "y2": round(y2, 2)
                    }
                })

            all_frames.append({
                "frame": frame_number,
                "vehicles": frame_detections
            })

        return all_frames