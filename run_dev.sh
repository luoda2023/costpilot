#!/usr/bin/env bash
# 造价通 - 一键启动开发环境(后端 + 前端 + Electron 桌面壳)
# 用户需填好 config.yaml 的 ai.api_key 后双击此脚本

set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "造价通 CostPilot v0.2.1 - 一键启动"
echo "============================================================"

# 1. 检测 Python
if ! command -v python >/dev/null 2>&1; then
  echo "[FAIL] 未检测到 python。请先安装 Python 3.10+"
  exit 1
fi
echo "[1/4] Python: $(python --version 2>&1)"

# 2. 检测依赖(关键包)
NEEDED_PKGS=("fastapi" "uvicorn" "openpyxl" "python-docx" "pyyaml" "sqlalchemy" "requests")
MISSING=()
for p in "${NEEDED_PKGS[@]}"; do
  if ! python -c "import $p" 2>/dev/null; then
    MISSING+=("$p")
  fi
done
if [ ${#MISSING[@]} -gt 0 ]; then
  echo "    缺少 Python 依赖: ${MISSING[*]}"
  echo "    正在 pip install ..."
  pip install --quiet "${MISSING[@]}" 2>&1 | tail -3
fi

# 3. 检测 Node
if ! command -v npm >/dev/null 2>&1; then
  echo "[FAIL] 未检测到 npm。请先安装 Node.js 18+"
  exit 1
fi
echo "[2/4] Node: $(node --version 2>&1) / npm: $(npm --version 2>&1)"

# 4. 检测 Electron 依赖
if [ ! -d node_modules ]; then
  echo "    首次运行,安装根 npm 依赖(electron + electron-builder + concurrently + wait-on)..."
  npm install --silent 2>&1 | tail -3
fi
if [ ! -d apps/web/node_modules ]; then
  echo "    首次运行,安装前端 npm 依赖..."
  (cd apps/web && npm install --silent 2>&1 | tail -3)
fi

# 5. 检测数据库
if [ ! -f data/sqlite/造价通.db ]; then
  echo "    首次运行,执行 alembic 迁移..."
  alembic upgrade head 2>&1 | tail -3
  echo "    导入价格库 + 模板..."
  python scripts/import_prices_to_db.py 2>&1 | tail -3
  python scripts/import_templates_to_db.py 2>&1 | tail -3
fi

# 6. 检测 config.yaml
if [ ! -f config.yaml ]; then
  echo "[FAIL] 未找到 config.yaml。请按 README.md 复制 config.example.yaml 改一行 ai.api_key"
  exit 1
fi

echo "[3/4] 启动后端 FastAPI (127.0.0.1:8765) 后台任务"
echo "[4/4] 启动 Vite 前端 (127.0.0.1:5173) + Electron"
echo ""
echo "    浏览器(可选): http://127.0.0.1:5173"
echo "    API 文档:    http://127.0.0.1:8765/docs"
echo ""
echo "    按 Ctrl+C 退出全部"
echo "============================================================"
npm run dev
