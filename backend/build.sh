#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "========================================="
echo "  Edge Stress 后端打包脚本 (macOS)"
echo "========================================="

# --- 清理旧构建 ---
echo ""
echo "[1/4] 清理旧构建..."
rm -rf dist_backend dist build *.spec

# --- PyInstaller 打包 ---
echo ""
echo "[2/4] PyInstaller 打包..."

# app_edgeStress 作为文件夹打入 _internal/（保留 .py 源码，便于后续 py2pyd 加密）
# --exclude-module 防止 PyInstaller 将其嵌入 PYZ 存档
# 业务代码依赖的第三方库需要通过 --hidden-import 手动指定

uv run pyinstaller --onedir \
  --name edge_stress_backend \
  --add-data "app_edgeStress:app_edgeStress" \
  --exclude-module app_edgeStress \
  --hidden-import loguru \
  --hidden-import fastapi \
  --hidden-import pydantic \
  --hidden-import pandas \
  --hidden-import numpy \
  --hidden-import scipy \
  --hidden-import scipy.signal \
  --hidden-import scipy.signal._peak_finding \
  --hidden-import lxml \
  --hidden-import lxml.etree \
  --hidden-import lxml.html \
  --hidden-import bs4 \
  --hidden-import html5lib \
  --hidden-import openpyxl \
  --hidden-import jinja2 \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.protocols \
  --hidden-import uvicorn.protocols.http \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.http.h11_impl \
  --hidden-import uvicorn.protocols.http.httptools_impl \
  --hidden-import uvicorn.protocols.websockets \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import uvicorn.protocols.websockets.websockets_impl \
  --hidden-import uvicorn.protocols.websockets.wsproto_impl \
  --hidden-import uvicorn.lifespan \
  --hidden-import uvicorn.lifespan.on \
  --hidden-import uvicorn.lifespan.off \
  --hidden-import uvicorn.loops \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.loops.asyncio \
  --hidden-import multiprocessing \
  --collect-all matplotlib \
  --collect-submodules plotly \
  main.py

# --- 整理产物 ---
echo ""
echo "[3/4] 整理产物..."
mv dist/edge_stress_backend ./dist_backend
rm -rf dist build *.spec

echo ""
echo "打包完成，app_edgeStress .py 文件:"
find dist_backend/_internal/app_edgeStress -type f -name "*.py" | sort

# --- py2pyd 加密业务代码 ---
echo ""
echo "[4/4] py2pyd 加密业务代码..."

# 删除旧版 UI 代码和不需要的文件（如果被 --add-data 带进来了）
rm -rf dist_backend/_internal/app_edgeStress/ui
rm -f  dist_backend/_internal/app_edgeStress/module/EdgeStress.py
rm -f  dist_backend/_internal/app_edgeStress/module/calEdgeStress.py
rm -f  dist_backend/_internal/app_edgeStress/module/reportEdgeStress.py

# 加密 app_edgeStress 下的所有 .py 文件（递归、删除原文件、跳过确认）
uv run py2pyd -r -d --no-confirm dist_backend/_internal/app_edgeStress/

echo ""
echo "加密完成，最终文件:"
find dist_backend/_internal/app_edgeStress -type f \( -name "*.so" -o -name "*.pyd" -o -name "*.py" \) | sort

echo ""
echo "========================================="
echo "  全部完成！产物目录: dist_backend/"
echo "========================================="
echo ""
echo "测试运行:"
echo "  ./dist_backend/edge_stress_backend"
echo ""
