from pathlib import Path
from ultralytics import YOLO


class VehicleDetector:
    """
    TrafficSentinel vehicle detection service.

    Uses a YOLO model to detect common road vehicles:
    car, motorcycle, bus, and truck.
    """

    VEHICLE_CLASSES = {
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck",
    }

    def __init__(self, model_path="yolov8n.pt", confidence=0.40):
        """
        Initialize the YOLO detector.

        Args:
            model_path: Path to the YOLO model.
            confidence: Minimum confidence required for a detection.
        """
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect_image(self, image_path):
        """
        Detect vehicles in a single image.

        Returns:
            List of detected vehicles.
        """

        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        results = self.model.predict(
            source=str(image_path),
            conf=self.confidence,
            verbose=False
        )

        return self._process_results(results)

    def detect_video(self, video_path):
        """
        Detect vehicles in a video.

        Returns:
            List containing detections for each frame.
        """

        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(
                f"Video not found: {video_path}"
            )

        results = self.model.predict(
            source=str(video_path),
            conf=self.confidence,
            stream=True,
            verbose=False
        )

        all_frames = []

        for frame_number, result in enumerate(results):
            detections = self._process_result(result)

            all_frames.append({
                "frame": frame_number,
                "detections": detections
            })

        return all_frames

    def _process_results(self, results):
        """
        Process YOLO results returned for an image.
        """

        if not results:
            return []

        return self._process_result(results[0])

    def _process_result(self, result):
        """
        Convert YOLO's result into a simple JSON-friendly format.
        """

        detections = []

        if result.boxes is None:
            return detections

        for box in result.boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            # Ignore non-vehicle objects
            if class_id not in self.VEHICLE_CLASSES:
                continue

            coordinates = box.xyxy[0].tolist()

            x1, y1, x2, y2 = coordinates

            detections.append({
                "class_id": class_id,
                "vehicle_type": self.VEHICLE_CLASSES[class_id],
                "confidence": round(confidence, 3),
                "bounding_box": {
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "x2": round(x2, 2),
                    "y2": round(y2, 2)
                }
            })

        return detections