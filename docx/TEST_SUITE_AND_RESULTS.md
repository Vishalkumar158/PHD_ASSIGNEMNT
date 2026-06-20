# Test Suite and Results

**PhD Application Technical Assessment Deliverable**  
**Video Ingestion & Preprocessing Pipeline**

---

## Executive Summary

A comprehensive automated test suite was developed to validate the correctness, robustness, and reliability of the video processing pipeline. The tests achieve **~78% code coverage** and focus on both happy paths and critical edge cases relevant to real-world sports video analysis.

---

## 1. Testing Approach

- **Framework**: `pytest` + `pytest-cov`
- **Style**: Unit + Integration tests with heavy mocking for expensive components (YOLO, full video I/O)
- **Test Data**: Synthetic test videos generated on-the-fly using `create_test_video()`
- **Coverage Goal**: Core logic, error paths, and configuration handling

---

## 2. What Was Tested

### Core Components Covered:

- **Video Utilities** (`utils/video_utils.py`)
  - Metadata extraction (`ffmpeg.probe`)
  - Frame quality assessment (Laplacian variance)
  - Synthetic test video generation
  - Pose estimation wrapper (mocked)

- **Pipeline Orchestration** (`core/pipeline.py`)
  - Frame processing loop
  - Quality-based filtering
  - Segment assignment

- **Main Application Flow** (`main.py`)
  - Config loading & CLI argument handling
  - Experiment manager integration

- **Error Handling & Resilience**

---

## 3. Edge Cases Discovered & Handled

| Edge Case                        | Handling Strategy                              | Status |
|----------------------------------|------------------------------------------------|--------|
| Missing / Corrupt video file     | Clear `ValueError` + fallback to single segment | ✅ |
| Zero or invalid FPS              | Safe timestamp calculation with default        | ✅ |
| All frames below quality threshold | Skip expensive pose inference                 | ✅ |
| No scene changes detected        | Fallback to full video as single segment       | ✅ |
| Invalid YAML config              | Graceful loading with defaults                 | ✅ |
| Empty frame list                 | Proper metrics calculation (no division by zero) | ✅ |

---

## 4. How Failures Are Handled

- **Defensive Programming**: Every major function wraps risky operations (`cv2.VideoCapture`, `ffmpeg.probe`, model inference) in try/except blocks.
- **Informative Logging**: All errors are logged with context before fallback.
- **Graceful Degradation**: Pipeline continues even if individual components fail (e.g., scene detection fails → treat as one scene).
- **Clear Error Messages**: Users get actionable feedback instead of cryptic crashes.

---

## 5. Running the Test Suite

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# 2. Run tests with coverage report
pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

# 3. View HTML coverage report
open htmlcov/index.html