# Orange Pi 6 Plus AI CCTV System

A C-based, edge-AI CCTV surveillance system designed for the Orange Pi 6 Plus.

The system captures video from one or more IP cameras using RTSP, decodes the video stream, performs local AI inference using a YOLOv8 ONNX model, detects objects, tracks them across frames, optionally performs face recognition and ANPR, stores detection information, and generates alerts.

The complete application is designed to run locally on the Orange Pi without requiring cloud-based AI processing.

---

# 1. Project Overview

The objective of this project is to build a production-oriented AI CCTV system using:

* Orange Pi 6 Plus
* IP/RTSP cameras
* Linux
* C
* FFmpeg
* OpenCV
* ONNX Runtime C API
* YOLOv8 ONNX model
* PostgreSQL
* Redis
* libcurl
* POSIX threads
* systemd

The application is designed around a native C architecture rather than Python.

## Main capabilities

* RTSP camera streaming
* Video frame capture
* Video decoding
* Motion detection
* AI object detection
* Person detection
* Vehicle detection
* Animal detection
* Package detection
* Multi-object tracking
* Face detection/recognition
* Automatic number plate recognition
* Event generation
* PostgreSQL detection storage
* Redis event/alert messaging
* Telegram notifications
* Local AI processing
* Multi-camera support
* Automatic startup using systemd
* Hardware-accelerated AI path where supported

---

# 2. High-Level Architecture

```text
                    ┌─────────────────────────┐
                    │      IP / RTSP Camera   │
                    │                         │
                    │  Camera 1               │
                    │  Camera 2               │
                    │  Camera 3               │
                    │  Camera 4 ...           │
                    └────────────┬────────────┘
                                 │
                              RTSP
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     RTSP Capture        │
                    │     rtsp_capture.c      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Video Decoder       │
                    │       FFmpeg             │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      Frame Buffer        │
                    │     RGB / BGR Frame      │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
       ┌───────────────────┐          ┌──────────────────┐
       │ Motion Detection  │          │   AI Detection   │
       │                   │          │     YOLOv8n      │
       └─────────┬─────────┘          └────────┬─────────┘
                 │                             │
                 └──────────────┬──────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │      Object Tracking    │
                    │     DeepSORT / Kalman   │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
        ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
        │     Face    │  │    ANPR     │  │ Event Engine│
        │ Recognition │  │ License     │  │             │
        │             │  │ Plate       │  │             │
        └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
               │                │                │
               └────────────────┼────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
             ┌─────────────┐        ┌─────────────┐
             │ PostgreSQL  │        │    Redis    │
             │ Database    │        │ Event Bus   │
             └─────────────┘        └──────┬──────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │ Telegram Alert  │
                                  └─────────────────┘
```

---

# 3. Hardware Requirements

## 3.1 Main Board

Recommended platform:

```text
Orange Pi 6 Plus
```

The original project targets the Orange Pi 6 Plus as the primary compute platform.

Recommended configuration:

| Component | Minimum               | Recommended                    |
| --------- | --------------------- | ------------------------------ |
| Board     | Orange Pi 6 Plus      | Orange Pi 6 Plus               |
| RAM       | 16 GB                 | 32 GB                          |
| Storage   | 256 GB NVMe           | 512 GB+ NVMe                   |
| Camera    | 1 RTSP camera         | 4–8 RTSP cameras               |
| Network   | Ethernet/Wi-Fi        | Gigabit Ethernet               |
| Power     | Suitable USB-C supply | Stable high-power USB-C supply |
| OS        | Ubuntu Linux          | Ubuntu 24.04                   |
| Cooling   | Basic heatsink        | Heatsink + active cooling      |

The original project recommends 16 GB minimum RAM and 32 GB recommended, with NVMe storage.

---

# 4. Required CCTV Hardware / Gadgets

## 4.1 IP Camera

The camera must support:

```text
RTSP
```

Examples:

* Dahua
* Hikvision
* Reolink
* TP-Link
* Amcrest
* Generic ONVIF/RTSP cameras

The project documentation specifies RTSP-compatible IP cameras.

Recommended camera specifications:

```text
Resolution : 1080p
FPS        : 15–30 FPS
Codec      : H.264 / H.265
Protocol   : RTSP
Network    : Ethernet preferred
```

---

# 5. Recommended Physical Setup

```text
              ┌─────────────────────┐
              │     IP Camera 1     │
              └──────────┬──────────┘
                         │ Ethernet
                         │
              ┌──────────▼──────────┐
              │                     │
              │   Network Switch    │
              │                     │
              └──────────┬──────────┘
                         │
                         │ Ethernet
                         │
              ┌──────────▼──────────┐
              │  Orange Pi 6 Plus   │
              │                     │
              │  AI CCTV Software   │
              └──────────┬──────────┘
                         │
                ┌────────┼────────┐
                │        │        │
                ▼        ▼        ▼
             NVMe     Network   Display
             Storage
```

For multiple cameras:

```text
Camera 1 ─┐
Camera 2 ─┤
Camera 3 ─┼──► Network Switch ──► Orange Pi 6 Plus
Camera 4 ─┤
Camera 5 ─┤
Camera 6 ─┘
```

---

# 6. Hardware Working Flow

The complete hardware/software path is:

```text
Camera Sensor
      │
      ▼
Camera ISP
      │
      ▼
H.264 / H.265 Encoder
      │
      ▼
Ethernet Network
      │
      ▼
RTSP Stream
      │
      ▼
Orange Pi Ethernet Controller
      │
      ▼
Linux Network Stack
      │
      ▼
FFmpeg
      │
      ▼
Video Decoder
      │
      ▼
Decoded Frame
      │
      ▼
Frame Buffer
      │
      ├───────────────► Motion Detection
      │
      ▼
Image Pre-processing
      │
      ▼
YOLOv8 ONNX
      │
      ▼
NPU / CPU Inference
      │
      ▼
Detection Results
      │
      ▼
Object Tracking
      │
      ├──────────────► Face Recognition
      │
      ├──────────────► ANPR
      │
      ▼
Event Generation
      │
      ├──────────────► PostgreSQL
      │
      ├──────────────► Redis
      │
      └──────────────► Telegram
```

---

# 7. Hardware Data Flow

A single camera frame follows this path:

```text
Camera
  │
  │ Video
  ▼
RTSP Packet
  │
  ▼
FFmpeg Demuxer
  │
  ▼
H.264/H.265 Decoder
  │
  ▼
Decoded YUV Frame
  │
  ▼
Image Conversion
  │
  ▼
RGB/BGR Frame
  │
  ▼
Resize
  │
  ▼
YOLO Input Tensor
  │
  ▼
AI Inference
  │
  ▼
Output Tensor
  │
  ▼
Post Processing
  │
  ▼
Bounding Boxes
  │
  ▼
Object Tracking
  │
  ▼
Event
```

---

# 8. CPU / Memory / AI Architecture

The Orange Pi acts as the central edge-computing platform.

```text
                 Orange Pi 6 Plus
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
       CPU            RAM           NPU*
        │              │              │
        │              │              │
        ▼              ▼              ▼
 Linux processes    Frame buffers   AI inference
 FFmpeg             Model memory    Acceleration
 PostgreSQL
 Redis
 CCTV application
```

`*` The NPU path depends on the available runtime, model conversion, and board/software support.

---

# 9. Project Directory

```text
orange-pi-ai-cctv/
│
├── models/
│   └── yolov8n.onnx
│
├── src/
│   │
│   ├── main.c
│   │
│   ├── camera/
│   │   ├── rtsp_capture.c
│   │   └── rtsp_capture.h
│   │
│   ├── detection/
│   │   ├── detector.c
│   │   └── detector.h
│   │
│   ├── motion/
│   │   ├── motion_detection.c
│   │   └── motion_detection.h
│   │
│   ├── tracking/
│   │   ├── deepsort.c
│   │   ├── deepsort.h
│   │   ├── tracker.c
│   │   ├── tracker.h
│   │   ├── kalman_filter.c
│   │   └── kalman_filter.h
│   │
│   ├── face/
│   │   ├── face_recognizer.c
│   │   └── face_recognizer.h
│   │
│   ├── anpr/
│   │   ├── anpr.c
│   │   └── anpr.h
│   │
│   ├── database/
│   │   ├── database.c
│   │   └── database.h
│   │
│   ├── alerts/
│   │   ├── telegram_bot.c
│   │   └── telegram_bot.h
│   │
│   ├── config/
│   │   ├── config.c
│   │   └── config.h
│   │
│   └── npu/
│       ├── npu_accelerator.c
│       └── npu_accelerator.h
│
├── include/
│
├── config/
│   └── config.json
│
├── scripts/
│   ├── setup.sh
│   └── install_service.sh
│
├── lib/
│
├── logs/
│
├── Makefile
│
└── README.md
```

---

# 10. C-Only Design

The target application does not use Python.

```text
Python                         C Replacement
------------------------------------------------
detector.py              →     detector.c
face_recognizer.py       →     face_recognizer.c
anpr.py                  →     anpr.c
telegram_bot.py          →     telegram_bot.c
database.py              →     database.c

deepsort.cpp             →     deepsort.c
tracker.cpp              →     tracker.c
npu_accelerator.cpp      →     npu_accelerator.c
```

The camera module remains:

```text
camera/
├── rtsp_capture.c
└── rtsp_capture.h
```

---

# 11. Camera Module

## rtsp_capture.h

This file exposes the camera API.

Responsibilities:

* RTSP configuration
* Camera context
* Frame structure
* Start capture
* Get frame
* Release frame
* Stop capture

## rtsp_capture.c

Responsibilities:

* RTSP connection
* Network stream handling
* FFmpeg initialization
* Stream discovery
* Video decoding
* Frame conversion
* Buffer management
* Error handling
* Cleanup

The camera module should not contain:

* YOLO
* Database
* Telegram
* Face recognition
* ANPR
* Tracking

This keeps the architecture modular.

---

# 12. AI Model

The project uses:

```text
models/yolov8n.onnx
```

The model is loaded by the C detection module through an ONNX-compatible native runtime.

```text
models/
└── yolov8n.onnx
```

AI flow:

```text
Decoded Frame
      │
      ▼
Resize
      │
      ▼
Normalize
      │
      ▼
Tensor Creation
      │
      ▼
ONNX Runtime
      │
      ▼
YOLOv8n
      │
      ▼
Output Tensor
      │
      ▼
Decode Predictions
      │
      ▼
Confidence Filtering
      │
      ▼
NMS
      │
      ▼
Bounding Boxes
```

---

# 13. Object Detection

YOLO is responsible for detecting objects inside each processed frame.

Example:

```text
Input:

1920 x 1080 camera frame

          ↓

Resize

          ↓

640 x 640

          ↓

YOLOv8

          ↓

Detection

Person:
confidence = 0.94
bbox = x1,y1,x2,y2

Car:
confidence = 0.89
bbox = x1,y1,x2,y2
```

The original project identifies people, cars, packages, animals and other object classes as detection targets.

---

# 14. Motion Detection

Motion detection provides an inexpensive first-stage event detector.

Typical flow:

```text
Frame N
   │
   ▼
Convert to Gray
   │
   ▼
Frame N-1
   │
   ▼
Absolute Difference
   │
   ▼
Threshold
   │
   ▼
Noise Removal
   │
   ▼
Motion Area
   │
   ▼
Motion Event
```

This can reduce unnecessary AI inference when there is no movement.

---

# 15. Object Tracking

Detection alone gives:

```text
Person detected
```

Tracking provides:

```text
Person ID = 17
```

Example:

```text
Frame 100 → Person ID 17
Frame 101 → Person ID 17
Frame 102 → Person ID 17
Frame 103 → Person ID 17
```

Tracking flow:

```text
YOLO Detection
      │
      ▼
Bounding Box
      │
      ▼
Feature / Motion Information
      │
      ▼
Kalman Filter
      │
      ▼
Association
      │
      ▼
Track ID
```

---

# 16. Face Recognition

Face recognition is an optional processing stage.

```text
Person Detected
      │
      ▼
Crop Person / Face Region
      │
      ▼
Face Detection
      │
      ▼
Face Alignment
      │
      ▼
Feature Extraction
      │
      ▼
Compare With Database
      │
      ▼
Known / Unknown
```

Example event:

```text
Person detected
Face detected
Identity: Known Person
Confidence: 0.91
```

---

# 17. ANPR

Automatic Number Plate Recognition:

```text
Vehicle Detection
       │
       ▼
Vehicle Bounding Box
       │
       ▼
Plate Region Detection
       │
       ▼
Crop Plate
       │
       ▼
Image Processing
       │
       ▼
OCR
       │
       ▼
License Plate Number
```

Example:

```text
Vehicle
   ↓
Plate detected
   ↓
KA01AB1234
   ↓
ANPR Event
```

---

# 18. Event Processing

All detection modules generate events.

Example:

```text
OBJECT_DETECTED
MOTION_DETECTED
FACE_RECOGNIZED
UNKNOWN_PERSON
VEHICLE_DETECTED
LICENSE_PLATE_DETECTED
```

The event manager determines what action should be taken.

```text
Detection
   │
   ▼
Event Manager
   │
   ├── Store Database
   │
   ├── Publish Redis Event
   │
   ├── Save Image
   │
   └── Send Telegram Alert
```

---

# 19. Database Architecture

PostgreSQL stores detection information.

Example tables:

```text
detections
alerts
cameras
known_faces
license_plates
events
```

Detection record:

```text
id
camera_id
track_id
object_type
confidence
bbox_x1
bbox_y1
bbox_x2
bbox_y2
timestamp
image_path
```

The original project uses PostgreSQL for detection storage and defines a `detections` and `alerts` schema.

---

# 20. Redis

Redis is used as a lightweight event/message mechanism.

```text
CCTV Application
       │
       ▼
Redis
       │
       ├── alerts
       ├── events
       └── notifications
```

Example:

```text
Channel: alerts

{
    camera_id: 1,
    type: "PERSON_DETECTED",
    confidence: 0.94
}
```

---

# 21. Telegram Alert

When an important event occurs:

```text
Camera
  ↓
Detection
  ↓
Event
  ↓
Alert Manager
  ↓
Telegram API
  ↓
Mobile Phone
```

Example:

```text
🚨 CCTV ALERT

Camera: Front Door
Event: Person Detected
Confidence: 94%
Time: 10:42:18
```

The original project defines Telegram as an optional alert mechanism.

---

# 22. Multithreaded Architecture

A native C implementation should use POSIX threads.

Recommended thread model:

```text
                  Main Thread
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
 Camera Thread   AI Thread     Event Thread
        │             │             │
        ▼             ▼             ▼
 RTSP Capture    YOLO Model     Database
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
                 Alert Thread
                      │
                      ▼
                   Telegram
```

Frame queues should be protected using:

```text
pthread_mutex
pthread_cond
```

---

# 23. Buffer Architecture

The camera thread should not directly block the AI thread.

Recommended:

```text
Camera
  │
  ▼
Capture Buffer
  │
  ▼
Frame Queue
  │
  ├─────────────► AI Thread
  │
  └─────────────► Motion Thread
```

Ring buffer concept:

```text
+-----+-----+-----+-----+-----+
| F0  | F1  | F2  | F3  | F4  |
+-----+-----+-----+-----+-----+
  ↑                       ↑
 Read                    Write
```

This prevents unnecessary memory allocation for every frame.

---

# 24. Configuration

Configuration should be stored outside the executable.

Example:

```text
/etc/cctv/config.json
```

Example:

```json
{
    "cameras": [
        {
            "id": 0,
            "name": "Front Door",
            "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream1",
            "width": 1920,
            "height": 1080,
            "fps": 30
        }
    ],

    "database": {
        "host": "localhost",
        "port": 5432,
        "user": "cctv",
        "password": "cctv123",
        "name": "cctv"
    },

    "model": {
        "yolo_path": "/opt/cctv/models/yolov8n.onnx",
        "confidence_threshold": 0.5
    },

    "hardware": {
        "use_npu": false,
        "threads": 4
    }
}
```

---

# 25. Required Software

Install build tools:

```bash
sudo apt update

sudo apt install -y \
    build-essential \
    gcc \
    make \
    cmake \
    pkg-config \
    git \
    wget \
    curl
```

Install FFmpeg development libraries:

```bash
sudo apt install -y \
    libavformat-dev \
    libavcodec-dev \
    libavutil-dev \
    libswscale-dev \
    libavdevice-dev \
    libavfilter-dev
```

Install OpenCV:

```bash
sudo apt install -y \
    libopencv-dev
```

Install PostgreSQL:

```bash
sudo apt install -y \
    postgresql \
    postgresql-contrib \
    libpq-dev
```

Install Redis:

```bash
sudo apt install -y \
    redis-server \
    libhiredis-dev
```

Install libcurl:

```bash
sudo apt install -y \
    libcurl4-openssl-dev
```

---

# 26. ONNX Runtime

The C application should use the native ONNX Runtime C API.

Required:

```text
ONNX Runtime
        │
        ▼
libonnxruntime.so
        │
        ▼
C API
        │
        ▼
detector.c
```

Do not install or use:

```text
Python
onnxruntime Python package
ultralytics Python package
```

for the final C-only application.

---

# 27. Model Installation

Create model directory:

```bash
mkdir -p models
```

Place:

```text
models/yolov8n.onnx
```

Verify:

```bash
ls -lh models/yolov8n.onnx
```

The original project also places the YOLO ONNX model under a dedicated model directory.

---

# 28. Database Setup

Start PostgreSQL:

```bash
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

Create database:

```bash
sudo -u postgres psql
```

Then:

```sql
CREATE USER cctv WITH PASSWORD 'cctv123';

CREATE DATABASE cctv OWNER cctv;

\c cctv
```

Create detections table:

```sql
CREATE TABLE detections (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER,
    track_id INTEGER,
    object_type VARCHAR(50),
    confidence FLOAT,
    bbox_x1 FLOAT,
    bbox_y1 FLOAT,
    bbox_x2 FLOAT,
    bbox_y2 FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT
);
```

Create alerts table:

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50),
    severity INTEGER,
    message TEXT,
    camera_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

# 29. Redis Setup

Start Redis:

```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

Test:

```bash
redis-cli ping
```

Expected:

```text
PONG
```

---

# 30. Build

From project root:

```bash
make clean
make
```

Expected executable:

```text
build/cctv
```

or:

```text
bin/cctv
```

depending on the Makefile configuration.

---

# 31. Example Makefile Architecture

The build system should compile:

```text
main.c
rtsp_capture.c
detector.c
motion_detection.c
deepsort.c
tracker.c
kalman_filter.c
face_recognizer.c
anpr.c
database.c
telegram_bot.c
config.c
npu_accelerator.c
```

and link against:

```text
pthread
FFmpeg
OpenCV
ONNX Runtime
PostgreSQL
Redis
libcurl
```

---

# 32. Application Startup

The application starts from:

```text
main.c
```

Startup sequence:

```text
main()
 │
 ├── Load configuration
 │
 ├── Initialize logging
 │
 ├── Initialize database
 │
 ├── Initialize Redis
 │
 ├── Load YOLO model
 │
 ├── Initialize camera
 │
 ├── Initialize motion detection
 │
 ├── Initialize tracker
 │
 ├── Initialize alert system
 │
 ├── Create worker threads
 │
 └── Start processing
```

---

# 33. Runtime Processing Flow

```text
main.c
  │
  ▼
Load Config
  │
  ▼
Open RTSP Camera
  │
  ▼
Capture Frame
  │
  ▼
Decode Frame
  │
  ▼
Motion Detection
  │
  ├── No Motion ──────► Continue
  │
  └── Motion
        │
        ▼
     AI Detection
        │
        ▼
     YOLO Result
        │
        ▼
     NMS / Filtering
        │
        ▼
     Tracking
        │
        ├── Person
        │
        ├── Vehicle
        │
        ├── Animal
        │
        └── Other Object
        │
        ▼
     Event Manager
        │
        ├── Database
        ├── Redis
        ├── Image
        └── Telegram
```

---

# 34. Complete Hardware-to-Software Flow

```text
                     PHYSICAL WORLD
                           │
                           ▼
                  ┌────────────────┐
                  │ Camera Sensor  │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ Camera ISP     │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ H.264/H.265    │
                  │ Encoder        │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ Ethernet       │
                  │ Network        │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ Orange Pi      │
                  │ Ethernet       │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ Linux Kernel   │
                  │ Network Stack  │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ FFmpeg         │
                  │ RTSP + Decode  │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ Frame Buffer   │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ AI Preprocess  │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ YOLOv8 ONNX    │
                  │ AI Inference   │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ Post Process   │
                  └───────┬────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │ Object Tracker │
                  └───────┬────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
           Face          ANPR        Events
             │            │            │
             └────────────┼────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Event Management │
                 └────────┬─────────┘
                          │
             ┌────────────┼─────────────┐
             ▼            ▼             ▼
        PostgreSQL       Redis       Telegram
```

---

# 35. Linux Boot and Application Startup

When the Orange Pi powers on:

```text
Power ON
   │
   ▼
Boot ROM
   │
   ▼
Bootloader
   │
   ▼
Linux Kernel
   │
   ▼
Device Drivers
   │
   ▼
Root Filesystem
   │
   ▼
systemd
   │
   ▼
PostgreSQL
Redis
Network
   │
   ▼
cctv.service
   │
   ▼
main()
   │
   ▼
AI CCTV System
```

---

# 36. systemd Service

Create:

```text
/etc/systemd/system/cctv.service
```

Example:

```ini
[Unit]
Description=Orange Pi AI CCTV System
After=network-online.target postgresql.service redis-server.service
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cctv
Environment="LD_LIBRARY_PATH=/opt/cctv/lib"
ExecStart=/opt/cctv/bin/cctv
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload

sudo systemctl enable cctv

sudo systemctl start cctv
```

---

# 37. Checking the Service

```bash
sudo systemctl status cctv
```

Live logs:

```bash
sudo journalctl -u cctv -f
```

Restart:

```bash
sudo systemctl restart cctv
```

Stop:

```bash
sudo systemctl stop cctv
```

---

# 38. Camera Testing

Before starting the C application, test the RTSP stream.

```bash
ffplay "rtsp://admin:password@192.168.1.100:554/stream1"
```

If the video displays correctly:

```text
Camera
   ↓
Network
   ↓
RTSP
   ↓
FFmpeg
```

is working.

The original project also recommends testing RTSP connectivity with `ffplay`.

---

# 39. Camera Configuration

Example:

```text
Camera 0
Name      : Front Door
IP        : 192.168.1.100
Port      : 554
Protocol  : RTSP
Resolution: 1920x1080
FPS       : 30
```

Example URL:

```text
rtsp://admin:password@192.168.1.100:554/stream1
```

---

# 40. Multi-Camera Architecture

For multiple cameras:

```text
Camera 1 ──► Capture Thread 1 ──► Frame Queue 1
Camera 2 ──► Capture Thread 2 ──► Frame Queue 2
Camera 3 ──► Capture Thread 3 ──► Frame Queue 3
Camera 4 ──► Capture Thread 4 ──► Frame Queue 4
                                      │
                                      ▼
                                AI Scheduler
                                      │
                                      ▼
                                YOLO Inference
```

Each camera should have:

```text
camera_id
capture context
frame queue
configuration
tracking context
statistics
```

---

# 41. Performance Optimization

Important optimization areas:

## Capture

* Avoid unnecessary frame copies
* Use FFmpeg efficiently
* Use bounded queues
* Drop old frames when latency becomes high

## AI

* Resize frames before inference
* Use appropriate input resolution
* Skip frames when necessary
* Use hardware acceleration where supported
* Batch inference only when it improves throughput

## Memory

* Reuse frame buffers
* Avoid repeated malloc/free
* Use ring buffers
* Keep model loaded in memory

## Threads

Separate:

```text
Capture
Decode
Motion
AI
Tracking
Database
Alert
```

---

# 42. Frame Dropping Strategy

For real-time CCTV, processing the newest frame is often more important than processing every frame.

Example:

```text
Camera produces:

F1 F2 F3 F4 F5 F6 F7 F8 F9

AI is still processing F3

Instead of processing:

F4 → F5 → F6 → F7

discard old frames and process:

F8 or F9
```

This keeps latency low.

---

# 43. Error Handling

The C application should handle:

```text
RTSP connection failure
Camera disconnect
Network timeout
Invalid frame
Decoder failure
AI model failure
Database failure
Redis failure
Telegram failure
Memory allocation failure
Thread creation failure
```

Example recovery:

```text
Camera disconnected
       │
       ▼
Detect error
       │
       ▼
Close connection
       │
       ▼
Wait 5 seconds
       │
       ▼
Reconnect
       │
       ▼
Resume capture
```

---

# 44. Logging

Recommended log levels:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Example:

```text
[INFO] CCTV application started
[INFO] Loading configuration
[INFO] Loading YOLO model
[INFO] Connecting camera 0
[INFO] RTSP stream connected
[INFO] AI inference started
[INFO] Person detected
[INFO] Detection stored
[ERROR] Camera connection lost
[INFO] Reconnecting camera
```

---

# 45. Debugging

Compile with debugging symbols:

```bash
make CFLAGS="-g -O0"
```

Run using GDB:

```bash
gdb ./bin/cctv
```

Useful commands:

```text
run
break main
continue
next
step
print
backtrace
info threads
thread
```

For memory problems:

```bash
valgrind ./bin/cctv
```

---

# 46. Useful Linux Debugging Commands

CPU:

```bash
top
```

Memory:

```bash
free -h
```

Processes:

```bash
ps aux
```

Disk:

```bash
df -h
```

Network:

```bash
ip addr
```

Network connections:

```bash
ss -tulpn
```

USB:

```bash
lsusb
```

Kernel messages:

```bash
dmesg
```

---

# 47. Monitoring

The system should expose runtime statistics:

```text
Camera FPS
Decoded FPS
AI FPS
Dropped Frames
Inference Time
CPU Usage
Memory Usage
NPU Usage
Detection Count
Tracking Count
RTSP Reconnect Count
```

Example:

```text
---------------------------------
AI CCTV STATUS
---------------------------------
Camera FPS       : 30
Processing FPS   : 15
AI FPS           : 12
Dropped Frames   : 4
Inference Time   : 82 ms
Objects          : 5
Active Tracks    : 3
CPU Usage        : 45%
Memory Usage     : 2.1 GB
---------------------------------
```

---

# 48. Security Considerations

Do not store production passwords directly in source code.

Avoid:

```text
rtsp://admin:password@camera
```

inside C source files.

Use:

```text
/etc/cctv/config.json
```

with appropriate permissions.

Example:

```bash
sudo chmod 600 /etc/cctv/config.json
```

The same applies to:

```text
Database password
Telegram token
Camera password
```

---

# 49. Complete Application Sequence

```text
                 POWER ON
                    │
                    ▼
                Linux Boot
                    │
                    ▼
                  systemd
                    │
                    ▼
              Start CCTV Service
                    │
                    ▼
                 main.c
                    │
                    ▼
              Load Configuration
                    │
                    ▼
            Initialize Subsystems
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    Camera       Database       Redis
       │
       ▼
    Load AI Model
       │
       ▼
    Create Threads
       │
       ▼
    Capture RTSP
       │
       ▼
    Decode Frame
       │
       ▼
    Motion Detection
       │
       ▼
    YOLO Detection
       │
       ▼
    Object Tracking
       │
       ├──────► Face Recognition
       │
       ├──────► ANPR
       │
       ▼
    Event Generation
       │
       ├──────► PostgreSQL
       │
       ├──────► Redis
       │
       └──────► Telegram
       │
       ▼
    Continue Processing
```

---

# 50. Troubleshooting

## Camera does not connect

Test:

```bash
ffplay "rtsp://user:password@camera-ip:554/stream"
```

Check:

```bash
ping <camera-ip>
```

Check RTSP port:

```bash
nc -zv <camera-ip> 554
```

---

## High CPU usage

Possible causes:

```text
Too many cameras
High resolution
High FPS
AI inference on CPU
Excessive frame copies
```

Solutions:

```text
Reduce input resolution
Reduce inference FPS
Drop old frames
Enable supported hardware acceleration
Use smaller AI model
```

---

## AI model not loading

Check:

```bash
ls -lh models/yolov8n.onnx
```

Check library:

```bash
ldd ./bin/cctv
```

Check:

```text
libonnxruntime.so
```

---

## Database unavailable

Check:

```bash
sudo systemctl status postgresql
```

Test:

```bash
sudo -u postgres psql -d cctv
```

---

## Redis unavailable

Check:

```bash
sudo systemctl status redis-server
```

Test:

```bash
redis-cli ping
```

Expected:

```text
PONG
```

---

## Telegram notification failure

Check:

```text
Telegram token
Chat ID
Internet connectivity
libcurl
```

---

# 51. Development Roadmap

## Phase 1 — Camera

```text
rtsp_capture.c
rtsp_capture.h
```

Goal:

```text
RTSP → Decode → Frame
```

## Phase 2 — Motion

```text
motion_detection.c
motion_detection.h
```

Goal:

```text
Frame → Motion Event
```

## Phase 3 — AI

```text
detector.c
detector.h
```

Goal:

```text
Frame → YOLO → Detection
```

## Phase 4 — Tracking

```text
tracker.c
deepsort.c
kalman_filter.c
```

Goal:

```text
Detection → Track ID
```

## Phase 5 — Database

```text
database.c
database.h
```

Goal:

```text
Detection → PostgreSQL
```

## Phase 6 — Alerts

```text
telegram_bot.c
telegram_bot.h
```

Goal:

```text
Event → Telegram
```

## Phase 7 — Advanced AI

```text
face_recognizer.c
anpr.c
npu_accelerator.c
```

Goal:

```text
Person → Face
Vehicle → Plate
AI → Hardware Acceleration
```

## Phase 8 — Production

```text
systemd
logging
watchdog
reconnect
performance monitoring
security
```

---

# 52. Final Target Architecture

```text
                      ORANGE PI 6 PLUS
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                     Linux / Ubuntu                         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    CCTV Application                   │  │
│  │                                                       │  │
│  │                     main.c                            │  │
│  │                       │                               │  │
│  │       ┌───────────────┼───────────────┐               │  │
│  │       ▼               ▼               ▼               │  │
│  │    Camera            Motion          Config            │  │
│  │       │               │                               │  │
│  │       ▼               ▼                               │  │
│  │    FFmpeg          Frame Analysis                     │  │
│  │       │                                               │  │
│  │       ▼                                               │  │
│  │   Frame Queue                                          │  │
│  │       │                                               │  │
│  │       ▼                                               │  │
│  │    YOLOv8                                               │  │
│  │       │                                               │  │
│  │       ▼                                               │  │
│  │   Detection                                            │  │
│  │       │                                               │  │
│  │       ▼                                               │  │
│  │    Tracker                                             │  │
│  │       │                                               │  │
│  │   ┌───┴──────────┐                                     │  │
│  │   ▼              ▼                                     │  │
│  │ Face            ANPR                                   │  │
│  │   │              │                                     │  │
│  │   └──────┬───────┘                                     │  │
│  │          ▼                                             │  │
│  │       Events                                            │  │
│  │          │                                             │  │
│  │    ┌─────┼──────┐                                      │  │
│  │    ▼     ▼      ▼                                      │  │
│  │   SQL   Redis Telegram                                  │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│          CPU        RAM        NPU        NVMe               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                           Ethernet
                              │
                    ┌─────────┴─────────┐
                    │                   │
                 Camera 1            Camera 2
                    │                   │
                    └────── RTSP ───────┘
```

---

# 53. Project Goal

The final system is intended to provide:

```text
Real-time
     +
Local AI
     +
C implementation
     +
Embedded Linux
     +
Hardware acceleration
     +
RTSP cameras
     +
Object detection
     +
Object tracking
     +
Face recognition
     +
ANPR
     +
Database
     +
Alerts
```

The key design principle is:

> **Capture locally → Process locally → Detect locally → Track locally → Store locally → Alert remotely**

No cloud AI processing is required for the core CCTV pipeline.

---

# 54. Quick Start

```bash
git clone <repository>

cd orange-pi-ai-cctv

mkdir -p models

# Place YOLO model
cp yolov8n.onnx models/

# Install dependencies
./scripts/setup.sh

# Build
make

# Test camera
ffplay "rtsp://user:password@camera-ip:554/stream"

# Run
sudo ./bin/cctv
```

For production:

```bash
sudo systemctl enable cctv
sudo systemctl start cctv
```

Check:

```bash
sudo systemctl status cctv
```

View logs:

```bash
sudo journalctl -u cctv -f
```

---

# 55. Summary

This project converts the original mixed Python/C/C++ CCTV concept into a native C-oriented embedded AI architecture.

The core pipeline is:

```text
RTSP Camera
     ↓
FFmpeg
     ↓
Frame Buffer
     ↓
Motion Detection
     ↓
YOLOv8 ONNX
     ↓
Object Detection
     ↓
Object Tracking
     ↓
Face / ANPR
     ↓
Event Manager
     ↓
PostgreSQL + Redis
     ↓
Telegram
```

The target implementation is designed for:

```text
Orange Pi 6 Plus
Ubuntu Linux
Native C
FFmpeg
OpenCV
ONNX Runtime C API
PostgreSQL
Redis
libcurl
POSIX Threads
systemd
```

The camera module remains intentionally small:

```text
camera/
├── rtsp_capture.c
└── rtsp_capture.h
```

This separation allows the RTSP camera subsystem to be developed and tested independently from the AI, tracking, database, and alert subsystems.
