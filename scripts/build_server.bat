@echo off
REM 造价通 - 用 PyInstaller 把后端打成单 EXE (CI 跑,本地原则不跑)
REM 产出: dist/costpilot-server.exe (约 80 MB)
cd /d "%~dp0\.."

echo === 1. 装 PyInstaller (如未装) ===
python -c "import PyInstaller" 2>nul || pip install --quiet pyinstaller

echo === 2. 清理旧产物 ===
if exist build rmdir /s /q build
if exist dist\costpilot-server.exe del /q dist\costpilot-server.exe

echo === 3. PyInstaller ===
pyinstaller costpilot-server.spec --noconfirm --log-level WARN

echo === 4. 验证产物 ===
if exist dist\costpilot-server.exe (
  for %%I in (dist\costpilot-server.exe) do echo 产出: dist\costpilot-server.exe  %%~zI bytes
) else (
  echo [FAIL] dist\costpilot-server.exe 未产出
  exit /b 1
)
