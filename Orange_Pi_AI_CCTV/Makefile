# Makefile
CC = gcc
CXX = g++
CFLAGS = -Wall -O2 -fPIC -I./include
CXXFLAGS = -Wall -O2 -fPIC -I./include -std=c++11
LDFLAGS = -shared
LIBS = -lavformat -lavcodec -lavutil -lswscale -lpthread -lm

# Directories
SRC_C = src/c
SRC_CPP = src/cpp
LIB_DIR = lib
INCLUDE_DIR = include

# C sources
C_SOURCES = $(SRC_C)/rtsp_capture.c $(SRC_C)/motion_detection.c $(SRC_C)/framerate_controller.c $(SRC_C)/ring_buffer.c
C_OBJECTS = $(C_SOURCES:$(SRC_C)/%.c=$(LIB_DIR)/%.o)
C_LIB = $(LIB_DIR)/librtsp_capture.so

# C++ sources
CPP_SOURCES = $(SRC_CPP)/deepsort.cpp $(SRC_CPP)/tracker.cpp $(SRC_CPP)/yolov8_inference.cpp $(SRC_CPP)/npu_accelerator.cpp
CPP_OBJECTS = $(CPP_SOURCES:$(SRC_CPP)/%.cpp=$(LIB_DIR)/%.o)
CPP_LIB = $(LIB_DIR)/libdeepsort.so

# Build everything
all: dirs $(C_LIB) $(CPP_LIB)

dirs:
	mkdir -p $(LIB_DIR)

# C library
$(C_LIB): $(C_OBJECTS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LIBS)

$(LIB_DIR)/%.o: $(SRC_C)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# C++ library
$(CPP_LIB): $(CPP_OBJECTS)
	$(CXX) $(LDFLAGS) -o $@ $^ $(LIBS)

$(LIB_DIR)/%.o: $(SRC_CPP)/%.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Python bindings
python-bindings:
	cd src/python && python setup.py build_ext --inplace

# Install system-wide
install:
	sudo cp $(LIB_DIR)/*.so /usr/local/lib/
	sudo ldconfig
	sudo cp -r src/python/* /usr/local/lib/python3.10/dist-packages/
	sudo mkdir -p /etc/cctv/
	sudo cp config.example.json /etc/cctv/config.json

# Clean
clean:
	rm -rf $(LIB_DIR)/*.o $(LIB_DIR)/*.so
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Run tests
test:
	cd tests && python test_system.py

# Development run
dev:
	sudo python src/python/detector.py

.PHONY: all dirs clean install test dev python-bindings
