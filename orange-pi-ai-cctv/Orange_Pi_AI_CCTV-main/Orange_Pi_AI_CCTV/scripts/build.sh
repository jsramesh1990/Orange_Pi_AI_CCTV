#!/bin/bash
# scripts/build.sh

set -e

echo "Building AI CCTV System for Orange Pi 6 Plus"
echo "============================================"

# Build C components
echo "Building C libraries..."
gcc -Wall -O2 -fPIC -I./include -c src/c/rtsp_capture.c -o lib/rtsp_capture.o
gcc -Wall -O2 -fPIC -I./include -c src/c/motion_detection.c -o lib/motion_detection.o
gcc -shared -o lib/librtsp_capture.so lib/rtsp_capture.o lib/motion_detection.o \
    -lavformat -lavcodec -lavutil -lswscale -lpthread

# Build C++ components
echo "Building C++ libraries..."
g++ -Wall -O2 -fPIC -I./include -std=c++11 -c src/cpp/deepsort.cpp -o lib/deepsort.o
g++ -Wall -O2 -fPIC -I./include -std=c++11 -c src/cpp/yolov8_inference.cpp -o lib/yolov8_inference.o
g++ -shared -o lib/libdeepsort.so lib/deepsort.o lib/yolov8_inference.o -lpthread

# Build NPU wrapper (if available)
if [ -f /usr/include/cix/cix_npu.h ]; then
    echo "Building NPU acceleration wrapper..."
    g++ -Wall -O2 -fPIC -I./include -std=c++11 -c src/cpp/npu_accelerator.cpp -o lib/npu_accelerator.o
    g++ -shared -o lib/libnpu_accelerator.so lib/npu_accelerator.o -lcix_npu
fi

# Build Python bindings
echo "Building Python bindings..."
cd src/python
python3 -m py_compile detector.py face_recognizer.py anpr.py telegram_bot.py

echo "Build complete!"
