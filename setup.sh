#!/bin/bash
# Setup script for Christmas Piano Lights on Raspberry Pi

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo "Making piano_lights.py executable..."
chmod +x piano_lights.py

echo "Setup complete! Run with: python3 piano_lights.py"
echo ""
echo "Note: Make sure your MIDI piano is connected via USB before running."