# Raspberry Pi Setup Guide for Christmas Piano Lights

## Check if Python is installed
```bash
python3 --version
pip3 --version
```

## Install required system packages
```bash
# Update package list
sudo apt update

# Install Python dev tools and audio libraries
sudo apt install python3-pip python3-dev libasound2-dev

# Install pygame dependencies
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
```

## Install Python packages
```bash
# Install from requirements.txt
pip3 install -r requirements.txt

# OR install manually:
pip3 install pygame RPi.GPIO
```

## Enable GPIO (if needed)
```bash
# Enable SPI and I2C (usually already enabled)
sudo raspi-config
# Navigate to: Interfacing Options -> Enable what you need
```

## Test MIDI detection
```bash
# List connected USB devices
lsusb

# Test if your piano is detected
python3 -c "import pygame.midi; pygame.midi.init(); print('MIDI devices:', [pygame.midi.get_device_info(i) for i in range(pygame.midi.get_count())])"
```

## Common Issues & Solutions

### Permission errors with GPIO:
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
# Log out and back in
```

### MIDI device not found:
- Make sure piano is connected via USB
- Try different USB port
- Check if piano is in MIDI mode (some have settings)

### Audio/MIDI conflicts:
```bash
# Kill any audio processes that might block MIDI
sudo pkill pulseaudio
```

## Run the script
```bash
python3 piano_lights.py
```