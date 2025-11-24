#!/usr/bin/env bash
# exit on error
set -o errexit

STORAGE_DIR=/opt/render/project/.render

if [[ ! -d $STORAGE_DIR/ffmpeg ]]; then
  echo "...Downloading FFmpeg..."
  mkdir -p $STORAGE_DIR/ffmpeg
  wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
  tar xvf ffmpeg-release-amd64-static.tar.xz -C $STORAGE_DIR/ffmpeg --strip-components 1
  rm ffmpeg-release-amd64-static.tar.xz
else
  echo "...Using cached FFmpeg..."
fi

# Add FFmpeg to PATH
export PATH=$STORAGE_DIR/ffmpeg:$PATH

# Install Python dependencies
pip install -r requirements.txt
