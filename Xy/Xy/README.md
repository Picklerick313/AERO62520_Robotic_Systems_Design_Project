# Robot Vision Project

A robot vision detection system based on YOLO and HSV color space, used to detect and recognize objects with different shapes and colors.

## Project Overview

This project can detect geometric shapes (cube, rectangle prism, triangle prism, cylinder, arch) and recognize colors using HSV color space (red, blue, yellow, etc.). The system can process images, video streams, and live camera input.

## Main Features

- **Shape Detection**：Use YOLO model to detect 5 geometric shapes
- **Color Recognition**：Color classification based on HSV color space
- **Combined Inference**：Output both shape and color information
- **Dataset Processing**：Analyze, split, and label dataset
- **RRealSense Support**：Extract frames from RealSense bag files

## Project Structure

```
robotproject/
├── datasets/              # Dataset folder
│   └── shapes/            # Shape detection dataset
│       ├── images/        # Training/validation/testing images
│       ├── labels/        # YOLO format labels
│       └── data.yaml      # Dataset configuration
├── tools/                 # Tool scripts
│   ├── color_utils.py           # HSV color estimation class
│   ├── color_labeling_tool.py   # Color labeling tool
│   ├── color_evaluate.py        # Color recognition evaluation
│   ├── infer_yolo_hsv.py        # YOLO + HSV combined inference
│   ├── analyze_dataset.py       # Dataset analysis
│   ├── split_yolo_dataset.py    # Dataset splitting tool
│   ├── rs_bag_to_frames.py      # RealSense bag to frames
│   ├── extract_frames_dedup.py  # Frame extraction and deduplication
│   ├── hsv_calibrate.py         # HSV color calibration
│   ├── hsv_adjust.py            # HSV parameter adjustment
│   └── color_ranges.yaml        # HSV color range configuration
├── runs/                  # Training and inference results
│   └── detect/            # YOLO detection results
├── outputs/               # Output folder
└── env_robot/             # Python virtual environment
```

## Environment Requirement

### Python Version
- Python 3.12

### Main Dependencies
- `ultralytics` - YOLO model training and inference
- `opencv-python` - Image processing
- `numpy` - Numerical computing
- `pyyaml` - Config file parsing
- `pyrealsense2` - RealSense camera support (optional)

## Dataset

### Dataset Format

The dataset uses YOLO format：
- Images：`images/train/`, `images/val/`, `images/test/`
- Labels：`labels/train/`, `labels/val/`, `labels/test/`
- Config：`data.yaml`

## Usage

### 1. Dataset Analysis

Count number of samples for each class：

```bash
python tools/analyze_dataset.py datasets/shapes/data.yaml
```

### 2. Dataset Split

Split dataset into train, validation, and test sets：

```bash
python tools/split_yolo_dataset.py \
  --images datasets/shapes/images_all/images \
  --labels datasets/shapes/images_all/labels \
  --out datasets/shapes \
  --train 0.8 --val 0.1 --test 0.1
```

### 3. Train YOLO Model

Use Ultralytics to train the model型：

```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')  # 或 yolov8s.pt, yolov8m.pt 等
model.train(
    data='datasets/shapes/data.yaml',
    epochs=100,
    imgsz=416,
    batch=16
)
```

### 4. Color Calibration

Calibrate HSV color ranges：

```bash
python tools/hsv_calibrate.py
```

### 5. Combined Inference (Shape + Color)

Use trained YOLO model and HSV color recognition for inference：

```bash
python tools/infer_yolo_hsv.py \
  --model runs/detect/train13/weights/best.pt \
  --source 0 \
  --hsv-config tools/color_ranges.yaml \
  --conf 0.25
```

### 6. Color Labeling

Label colors of detected objects：

```bash
python tools/color_labeling_tool.py
```

### 7. RealSense Frame Extraction

Extract frames from RealSense bag files：

```bash
python tools/rs_bag_to_frames.py \
  --bag path/to/your.bag \
  --out datasets/shapes/images_all \
  --fps 1.0 \
  --class-name cube \
  --scene scene1_bright
```

## Config Files

### data.yaml

Dataset configuration：

```yaml
path: /home/student24/robotproject/datasets/shapes
train: images/train
val: images/val
test: images/test
names:
  0: cube
  1: rectangle_prism
  2: triangle_prism
  3: cylinder
  4: arch
```

### color_ranges.yaml

HSV color range configuration：

```yaml
red:
  - [0, 120, 70, 10, 255, 255]
  - [170, 120, 70, 180, 255, 255]

blue:
  - [90, 50, 50, 130, 255, 255]

yellow:
  - [20, 80, 80, 35, 255, 255]

color_ratio_threshold:
  default: 0.18
  blue: 0.10
```

## Core Module

### HSVColorEstimator

Class in color_utils.py for HSV color estimation：

- `estimate_from_roi(bgr_roi)`: Estimate color from ROI
- `estimate_from_mask(bgr_img, mask)`: Estimate color from mask
- Support H channel wrapping (for red)
- Automatic morphological denoising

## Training Results

Training results are saved in runs/detect/ including：
- Training curves
- Confusion matrix
- Validation results
- Model weights


