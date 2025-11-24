#!/usr/bin/env bash
# 遇到錯誤就停止
set -e

echo "正在安裝 Python 套件..."
pip install -r requirements.txt

echo "正在下載相容的 FFmpeg..."
# 下載 Linux 伺服器專用的靜態版本 FFmpeg
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz

# 解壓縮
tar xvf ffmpeg-release-amd64-static.tar.xz

# 把 ffmpeg 執行檔移到專案根目錄，並重新命名為 ffmpeg
# 注意：這裡假設解壓出來的資料夾名稱格式，通常是 ffmpeg-版本號-amd64-static
mv ffmpeg-*-amd64-static/ffmpeg ./ffmpeg
mv ffmpeg-*-amd64-static/ffprobe ./ffprobe

# 清理下載的垃圾
rm -rf ffmpeg-*-amd64-static*

# 給予執行權限
chmod +x ./ffmpeg

echo "FFmpeg 安裝完成！"
