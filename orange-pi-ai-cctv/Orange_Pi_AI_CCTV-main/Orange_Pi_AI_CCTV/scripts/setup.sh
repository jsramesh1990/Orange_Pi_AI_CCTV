#!/bin/bash
# scripts/setup.sh

set -e

echo "========================================="
echo "Orange Pi 6 Plus AI CCTV System Setup"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

# Check if running on Orange Pi
if [ ! -f /etc/orangepi-release ]; then
    print_error "This script is designed for Orange Pi systems"
    exit 1
fi

# Install dependencies
print_info "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    libavformat-dev \
    libavcodec-dev \
    libavutil-dev \
    libswscale-dev \
    libopencv-dev \
    python3-dev \
    python3-pip \
    postgresql \
    postgresql-contrib \
    redis-server \
    libssl-dev \
    libcurl4-openssl-dev

# Install Python packages
print_info "Installing Python packages..."
pip3 install --upgrade pip
pip3 install \
    numpy \
    opencv-python \
    psycopg2-binary \
    redis \
    requests \
    python-telegram-bot \
    onnxruntime \
    ultralytics

# Build C/C++ libraries
print_info "Building C/C++ libraries..."
make clean
make all

# Setup PostgreSQL
print_info "Setting up PostgreSQL..."
sudo systemctl start postgresql
sudo -u postgres psql -c "CREATE USER cctv WITH PASSWORD 'cctv123';" || true
sudo -u postgres psql -c "CREATE DATABASE cctv OWNER cctv;" || truesudo -u postgres psql -d cctv -f database/schema.sql

# Setup Redis
print_info "Setting up Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Create directories
print_info "Creating directories..."
sudo mkdir -p /var/cctv/{snapshots,recordings,models,logs}
sudo mkdir -p /etc/cctv
sudo chown -R $USER:$USER /var/cctv

# Download YOLO model
print_info "Downloading YOLO model..."
if [ ! -f /var/cctv/models/yolov8n.onnx ]; then
    wget -O /var/cctv/models/yolov8n.onnx \
        https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.onnx
fi

# Create configuration
print_info "Creating configuration..."
cat > /tmp/config.json << 'EOF'
{
    "cameras": [],
    "database": {
        "host": "localhost",
        "port": 5432,
        "user": "cctv",
        "password": "cctv123",
        "name": "cctv"
    },
    "redis": {
        "host": "localhost",
        "port": 6379
    },
    "model": {
        "yolo_path": "/var/cctv/models/yolov8n.onnx",
        "face_model_path": "/var/cctv/models/face_model.dat"
    },
    "hardware": {
        "use_npu": false,
        "use_gpu": false,
        "threads": 4
    },
    "alerts": {
        "telegram_token": "",
        "telegram_chat_id": ""
    }
}
EOF

sudo mv /tmp/config.json /etc/cctv/config.json

# Create systemd service
print_info "Creating systemd service..."
cat > /tmp/cctv.service << 'EOF'
[Unit]
Description=AI CCTV System
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cctv
ExecStart=/usr/bin/python3 /opt/cctv/src/python/detector.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/cctv.service /etc/systemd/system/
sudo systemctl daemon-reload

# Copy source files
print_info "Copying source files..."
sudo mkdir -p /opt/cctv
sudo cp -r . /opt/cctv/

# Set permissions
sudo chmod +x /opt/cctv/scripts/*.sh

print_status "Setup complete!"

echo ""
echo "========================================="
echo "Next steps:"
echo "========================================="
echo ""
echo "1. Edit configuration:"
echo "   sudo nano /etc/cctv/config.json"
echo ""
echo "2. Add your cameras to the config"
echo ""
echo "3. Set Telegram credentials (optional):"
echo "   export TELEGRAM_TOKEN='your_token'"
echo "   export TELEGRAM_CHAT_ID='your_chat_id'"
echo ""
echo "4. Start the system:"
echo "   sudo systemctl start cctv"
echo ""
echo "5. Check logs:"
echo "   sudo journalctl -u cctv -f"
echo ""
echo "6. Monitor via Redis:"
echo "   redis-cli SUBSCRIBE alerts"
echo ""
echo "========================================="
