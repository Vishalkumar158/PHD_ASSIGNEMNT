from ultralytics import YOLO


class PoseInference:
    def __init__(self, config):
        model_path = config.get("model", {}).get("path", "yolov8n-pose.pt")
        self.model = YOLO(model_path)

    def predict(self, frame_path):
        results = self.model(frame_path, conf=0.5, verbose=False)
        return results[0].to_json() if results else {}