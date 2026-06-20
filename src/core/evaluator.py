import numpy as np


class PoseEvaluator:
    def compute_fps(self, total_frames, total_time):
        return total_frames / total_time if total_time > 0 else 0

    def summarize(self, stats):
        return {
            "avg_quality": float(np.mean(stats["quality"])) if stats["quality"] else 0,
            "fps": stats["fps"],
            "num_frames": stats["num_frames"]
        }