#!/usr/bin/env bash
# Build script for Render deployment
# This script installs FFmpeg on the Render server

set -e  # Exit on error

echo "===================="
echo "Installing FFmpeg..."
echo "===================="

# Update package list
apt-get update -y

# Install FFmpeg and FFprobe
apt-get install -y ffmpeg

# Verify installation
ffmpeg -version
ffprobe -version

echo "===================="
echo "FFmpeg installed successfully!"
echo "===================="

# Install Python dependencies
echo "===================="
echo "Installing Python dependencies..."
echo "===================="
pip install --upgrade pip
pip install -r requirements.txt

echo "===================="
echo "Build complete!"
echo "===================="
