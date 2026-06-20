import pytest
import os
import cv2
import numpy as np
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from utils.video_utils import extract_frames, assess_frame_quality, load_video_metadata

def create_test_video(path: str, duration_sec: int = 5, fps: int = 30):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, (640, 480))
    for i in range(duration_sec * fps):
        frame = np.zeros((480, 640, 3), np.uint8)
        cv2.putText(frame, f"Frame {i}", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        out.write(frame)
    out.release()

@pytest.fixture
def sample_video(tmp_path):
    vid_path = tmp_path / "test.mp4"
    create_test_video(str(vid_path))
    return str(vid_path)

def test_extract_frames(sample_video, tmp_path):
    out_dir = tmp_path / "frames"
    frames = extract_frames(sample_video, str(out_dir), interval=10)
    assert len(frames) > 0
    assert os.path.exists(frames[0]['path'])

def test_quality_assessment():
    frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    score = assess_frame_quality(frame)
    assert score >= 0