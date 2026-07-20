@echo off
REM 造价通 - 一键启动开发环境
cd /d "%~dp0"

echo ============================================================
echo 造价通 CostPilot v0.2.1 - 一键启动
echo ============================================================

where python >nul 2>nul
if errorlevel 1 (
  echo [FAIL] 未检测到 python。请先安装 Python 3.10+
  pause
  exit /b 1
)
python --version

REM 装关键依赖
for %%P in (fastapi uvicorn openpyxl python-docx pyyaml sqlalchemy requests) do (
  python -c "import %%P" 2>nul || (
    echo    缺 %%P,pip install ...
    pip install --quiet %%P
  )
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [FAIL] 未检测到 npm。请先安装 Node.js 18+
  pause
  exit /b 1
)
node --version
npm --version

if not exist node_modules (
  echo    首次运行,安装根 npm 依赖...
  call npm install --silent
)
if not exist apps\web\node_modules (
  echo    首次运行,安装前端依赖...
  cd apps\web
  call npm install --silent
  cd ..\..
)

if not exist "data\sqlite\造价通.db" (
  echo    首次运行,执行 alembic 迁移...
  call alembic upgrade head
  python scripts\import_prices_to_db.py
  python scripts\import_templates_to_db.py
)

if not exist config.yaml (
  echo [FAIL] 未找到 config.yaml
  pause
  exit /b 1
)

echo ============================================================
echo 启动中... 浏览器访问 http://127.0.0.1:5173
echo API 文档: http://127.0.0.1:8765/docs
echo Ctrl+C 退出
echo ============================================================
call npm run dev
pause
