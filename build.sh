#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. 安裝 Python 套件
pip install -r requirements.txt

# 2. 下載並設定 FFmpeg (因為 Render 預設沒有)
if [ ! -f ./ffmpeg ]; then
    echo "Downloading FFmpeg..."
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    tar xvf ffmpeg-release-amd64-static.tar.xz
    mv ffmpeg-*-amd64-static/ffmpeg ./ffmpeg
    chmod +x ./ffmpeg
    rm -rf ffmpeg-*-amd64-static*
    echo "FFmpeg installed."
fi
