#!/bin/bash
# scripts/run.sh

# Set environment variables
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:./lib
export PYTHONPATH=$PYTHONPATH:./src/python

# Load configuration
if [ -f /etc/cctv/config.json ]; then
    echo "Loading configuration from /etc/cctv/config.json"
else
    echo "Warning: No configuration found at /etc/cctv/config.json"
fi

# Start the system
echo "Starting AI CCTV System..."
python3 src/python/detector.py

# Handle cleanup
cleanup() {
    echo "Shutting down..."
    kill $!
    exit 0
}

trap cleanup SIGINT SIGTERM
wait
