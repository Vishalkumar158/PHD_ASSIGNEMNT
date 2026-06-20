import time
import cv2
from tqdm import tqdm

from .inference import PoseInference
from .evaluator import PoseEvaluator
from utils.video_utils import assess_frame_quality


class Pipeline:
    def __init__(self, config):
        self.config = config
        self.model = PoseInference(config)
        self.evaluator = PoseEvaluator()

    def run(self, frames_info, segments):
        manifest = []
        stats = {"quality": []}

        start_time = time.time()

        for frame_info in tqdm(frames_info, desc="Pipeline Running"):
            frame = cv2.imread(frame_info["path"])
            if frame is None:
                continue

            # Quality
            quality = assess_frame_quality(frame)
            frame_info["quality_score"] = float(quality)
            stats["quality"].append(quality)

            # Segment assignment
            frame_info["segment"] = next(
                (s["segment_id"] for s in reversed(segments)
                 if frame_info["timestamp"] >= s["start_time"]),
                0
            )

            # Inference
            if quality > self.config["processing"]["quality_threshold"]:
                pose = self.model.predict(frame_info["path"])
                frame_info["pose_estimation"] = pose
            else:
                frame_info["pose_estimation"] = None

            manifest.append(frame_info)

        total_time = time.time() - start_time

        metrics = self.evaluator.summarize({
            "quality": stats["quality"],
            "fps": self.evaluator.compute_fps(len(frames_info), total_time),
            "num_frames": len(frames_info)
        })

        return manifest, metrics