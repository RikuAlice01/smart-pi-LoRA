#!/bin/bash
# Quick start script for mockup mode

echo "🎭 Starting LoRa Node in Mockup Mode"
echo "===================================="

# Check if virtual environment exists
if [ -d "lora_env" ]; then
    echo "Activating virtual environment..."
    source lora_env/bin/activate
fi

# Check if mockup config exists, create if not
if [ ! -f "mockup_config.json" ]; then
    echo "Creating mockup configuration..."
    cp config.json mockup_config.json 2>/dev/null || echo "Using default config"
fi

# Start in mockup mode
echo "Starting mockup mode..."
echo "Press Ctrl+C to stop"
echo ""

python3 main.py mockup --config mockup_config.json --log-level INFO

echo ""
echo "Mockup mode stopped."
