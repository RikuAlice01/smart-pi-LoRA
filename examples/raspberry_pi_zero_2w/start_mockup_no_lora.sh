#!/bin/bash
# Quick start script for mockup mode without LoRa transmission

echo "🎭 Starting LoRa Node in Mockup Mode (No LoRa)"
echo "=============================================="

# Check if virtual environment exists
if [ -d "lora_env" ]; then
    echo "Activating virtual environment..."
    source lora_env/bin/activate
fi

# Start in mockup mode without LoRa
echo "Starting mockup mode (sensors only)..."
echo "Press Ctrl+C to stop"
echo ""

python3 main.py mockup --config mockup_config.json --no-lora --interval 3

echo ""
echo "Mockup mode stopped."
