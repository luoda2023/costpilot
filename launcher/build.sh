#!/usr/bin/env bash
# 造价通启动器 - Linux/Mac 交叉编译 Windows EXE (线上构建)
set -e

cd "$(dirname "$0")"

# 1. 检测 Go
if ! command -v go >/dev/null 2>&1; then
  echo "未检测到 Go。请先安装 Go 1.21+:  https://go.dev/dl/"
  exit 1
fi

echo "[1/4] Go 版本: $(go version)"

# 2. 装依赖
echo "[2/4] go mod tidy ..."
go mod tidy

# 3. 交叉编译 Windows EXE (无 cmd 黑框)
echo "[3/4] 交叉编译 Windows EXE ..."
mkdir -p dist
CGO_ENABLED=0 GOOS=windows GOARCH=amd64 \
  go build -ldflags="-s -w -H windowsgui" \
  -o dist/start.exe .

# 4. 输出信息
echo "[4/4] 完成:"
ls -lh dist/start.exe
echo
echo "把 dist/start.exe 和造价通本体 costpilot.exe 放同一目录,双击 start.exe 即可。"
