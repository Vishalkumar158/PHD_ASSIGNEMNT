# import argparse
# import yaml
# import logging
# from pathlib import Path
# import json
# from datetime import datetime
# import os

# from core.pipeline import Pipeline
# from core.experiment import ExperimentManager
# from utils.video_utils import (
#     load_video_metadata,
#     extract_frames,
#     detect_scene_changes
# )


# def setup_logging(log_file: str):
#     log_path = Path(log_file)
#     log_path.parent.mkdir(parents=True, exist_ok=True)

#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s - %(levelname)s - %(message)s",
#         handlers=[
#             logging.FileHandler(log_path, encoding="utf-8"),
#             logging.StreamHandler()
#         ]
#     )


# def main(config_path: str, input_video: str = None):
#     with open(config_path, "r") as f:
#         config = yaml.safe_load(f)

#     if input_video:
#         config["input"]["video_path"] = input_video

#     config["output"]["base_dir"] = config["output"]["base_dir"].strip("'\"")

#     setup_logging(config["logging"]["file"])
#     logger = logging.getLogger(__name__)

#     exp = ExperimentManager()
#     exp.save_config(config)

#     video_path = config["input"]["video_path"]

#     logger.info(f"Processing: {video_path}")

#     metadata = load_video_metadata(video_path)
#     logger.info(f"Metadata: {metadata}")

#     # base_output = Path(config["output"]["base_dir"])
#     # base_output.mkdir(parents=True, exist_ok=True)
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     base_output = Path(config['output']['base_dir']) / f"video_{timestamp}"
#     base_output.mkdir(parents=True, exist_ok=True)

#     frames_dir = base_output / "frames"
#     frames_dir.mkdir(exist_ok=True)

#     segments = detect_scene_changes(video_path, config["scene_detection"]["threshold"]) \
#         if config["scene_detection"]["enabled"] else []

#     frames_info = extract_frames(
#         video_path,
#         str(frames_dir),
#         interval=config["processing"]["frame_interval"],
#         target_res=tuple(config["processing"]["target_resolution"])
#     )

#     pipeline = Pipeline(config)
#     manifest, metrics = pipeline.run(frames_info, segments)

#     with open(base_output / "metadata.json", "w") as f:
#         json.dump(manifest, f, indent=2)

#     exp.save_results(manifest)
#     exp.save_metrics(metrics)

#     logger.info(f"Metrics: {metrics}")


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--config", default="Path to config file")
#     parser.add_argument("--input", help="Override video path")

#     args = parser.parse_args()
#     main(args.config, args.input)


import argparse
import yaml
import logging
from pathlib import Path
import json
from datetime import datetime
import os

from core.pipeline import Pipeline
from core.experiment import ExperimentManager
from utils.video_utils import (
    load_video_metadata,
    extract_frames,
    detect_scene_changes
)


def setup_logging(log_file: str):
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )


def main(config_path: str, input_video: str = None):
    # Load config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Override video path if provided via CLI
    if input_video:
        config["input"]["video_path"] = input_video

    # Clean output base dir
    config["output"]["base_dir"] = config["output"]["base_dir"].strip("'\"")

    setup_logging(config["logging"]["file"])
    logger = logging.getLogger(__name__)

    # Initialize experiment manager
    exp = ExperimentManager()
    exp.save_config(config)

    video_path = config["input"]["video_path"]
    logger.info(f"Processing video: {video_path}")

    # Load metadata
    metadata = load_video_metadata(video_path)
    logger.info(f"Video Metadata: {metadata}")

    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output = Path(config['output']['base_dir']) / f"video_{timestamp}"
    base_output.mkdir(parents=True, exist_ok=True)

    frames_dir = base_output / "frames"
    frames_dir.mkdir(exist_ok=True)

    # ====================== SCENE DETECTION & SPLITTING ======================
    scene_output_dir = None
    segments = []

    if config.get("scene_detection", {}).get("enabled", False):
        scene_output_dir = base_output / "scenes"
        segments = detect_scene_changes(
            video_path=video_path,
            threshold=config["scene_detection"].get("threshold", 27.0),
            output_dir=scene_output_dir if config["scene_detection"].get("split_scenes", True) else None
        )
        logger.info(f"Detected {len(segments)} scenes. Scene clips saved to: {scene_output_dir}")
    else:
        # Fallback: single segment for whole video
        segments = [{
            'segment_id': 0,
            'start_time': 0.0,
            'end_time': metadata.get('duration', 999999.0),
            'start_frame': 0,
            'end_frame': -1
        }]
        logger.info("Scene detection disabled. Treating video as single segment.")

    # ====================== FRAME EXTRACTION ======================
    frames_info = extract_frames(
        video_path,
        str(frames_dir),
        interval=config["processing"]["frame_interval"],
        target_res=tuple(config["processing"]["target_resolution"])
    )

    logger.info(f"Extracted {len(frames_info)} frames")

    # ====================== PIPELINE EXECUTION ======================
    pipeline = Pipeline(config)
    manifest, metrics = pipeline.run(frames_info, segments)

    # Save manifest
    with open(base_output / "metadata.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Save experiment results
    exp.save_results(manifest)
    exp.save_metrics(metrics)

    logger.info(f"Processing completed. Output saved to: {base_output}")
    logger.info(f"Metrics: {metrics}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sports Video Ingestion & Preprocessing Pipeline")
    parser.add_argument("--config", type=str, default="configs/config.yaml",
                        help="Path to config file")
    parser.add_argument("--input", type=str, help="Override input video path")

    args = parser.parse_args()
    main(args.config, args.input)