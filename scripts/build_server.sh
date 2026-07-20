#!/usr/bin/env bash
# 造价通 - Linux/Mac 跑 PyInstaller (本地或 CI 都可)
set -e
cd "$(dirname "$0")/.."

echo "=== 1. 装 PyInstaller ==="
python -c "import PyInstaller" 2>/dev/null || pip install --quiet pyinstaller

echo "=== 2. 清理旧产物 ==="
rm -rf build dist/costpilot-server.exe

echo "=== 3. PyInstaller ==="
pyinstaller costpilot-server.spec --noconfirm --log-level WARN

echo "=== 4. 验证产物 ==="
ls -lh dist/costpilot-server.exe
