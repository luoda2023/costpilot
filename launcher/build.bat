@echo off
REM 造价通启动器 - Windows 线上构建
setlocal
cd /d "%~dp0"

where go >nul 2>nul
if errorlevel 1 (
  echo 未检测到 Go。请先安装 Go 1.21+: https://go.dev/dl/
  exit /b 1
)

echo [1/4] Go 版本:
go version

echo [2/4] go mod tidy ...
go mod tidy

echo [3/4] 编译 Windows EXE ...
if not exist dist mkdir dist
go build -ldflags="-s -w -H windowsgui" -o dist\start.exe .

echo [4/4] 完成:
dir dist\start.exe

echo.
echo 把 dist\start.exe 和造价通本体 costpilot.exe 放同一目录,双击 start.exe 即可。
