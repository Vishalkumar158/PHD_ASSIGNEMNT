import cv2
import os
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import numpy as np
from ultralytics import YOLO
import ffmpeg
from scenedetect import detect, ContentDetector
from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg

logger = logging.getLogger(__name__)

def load_video_metadata(video_path: str) -> Dict:
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        if video_stream:
            return {
                'duration': float(video_stream.get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                'codec': video_stream.get('codec_name'),
                'format': probe.get('format', {}).get('format_name')
            }
        return {}
    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        return {}

def extract_frames(video_path: str, output_dir: str, interval: int = 30, 
                  target_res: Tuple[int, int] = (640, 360)) -> List[Dict]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    extracted = []
    os.makedirs(output_dir, exist_ok=True)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % interval == 0:
            resized = cv2.resize(frame, target_res)
            rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            frame_path = os.path.join(output_dir, f"frame_{frame_count:06d}.jpg")
            cv2.imwrite(frame_path, rgb_frame)
            
            extracted.append({
                'frame_index': frame_count,
                'timestamp': frame_count / fps if fps > 0 else 0,
                'path': frame_path,
                'resolution': target_res,
                'transformations': ['resize', 'bgr_to_rgb']
            })
        
        frame_count += 1
    
    cap.release()
    return extracted

def detect_scene_changes(video_path: str, threshold: float = 30.0) -> List[Dict]:
    scene_list = detect(video_path, ContentDetector(threshold=threshold))
    segments = []
    for i, scene in enumerate(scene_list):
        segments.append({
            'segment_id': i,
            'start_time': scene[0].get_seconds(),
            'end_time': scene[1].get_seconds()
        })
    return segments

def assess_frame_quality(frame: np.ndarray) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def run_yolo_pose(frame_path: str, model: Optional[YOLO] = None) -> Dict:
    if model is None:
        model = YOLO('yolov8n-pose.pt')
    results = model(frame_path, conf=0.5, verbose=False)
    return results[0].to_json() if results else {}


import logging
from typing import List, Dict
from pathlib import Path

from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg

logger = logging.getLogger(__name__)


def detect_scene_changes(
    video_path: str, 
    threshold: float = 27.0,
    output_dir: str = None
) -> List[Dict]:
    """
    Detect scene changes and optionally split video into scene clips.
    
    Returns list of segments with start/end times.
    If output_dir is provided, also creates split video files.
    """
    try:
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))
        
        logger.info(f"Detecting scenes with threshold={threshold}...")
        scene_manager.detect_scenes(video, show_progress=True)
        
        scene_list = scene_manager.get_scene_list()
        
        segments = []
        for i, (start, end) in enumerate(scene_list):
            segments.append({
                'segment_id': i,
                'start_time': start.get_seconds(),
                'end_time': end.get_seconds(),
                'start_frame': start.get_frames(),
                'end_frame': end.get_frames(),
            })
        
        # === SPLIT VIDEO INTO SCENES (Key Requirement) ===
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Splitting video into {len(scene_list)} scenes...")
            split_video_ffmpeg(
                video_path,
                scene_list,
                output_dir=str(output_dir),
                show_progress=True,
                # Optional: custom naming
                # prefix="scene_"
            )
            logger.info(f"Scene clips saved to: {output_dir}")
        
        return segments

    except Exception as e:
        logger.error(f"Scene detection failed: {e}")
        # Fallback: treat whole video as one segment
        return [{
            'segment_id': 0,
            'start_time': 0.0,
            'end_time': 999999.0,  # large number
            'start_frame': 0,
            'end_frame': -1
        }]