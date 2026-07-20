#!/usr/bin/env bash
# 造价通 - 一键启动内嵌 AI 聊天前端 LobeChat
# 推荐: Docker 一键起,无 Docker 用 Node 自部署

set -e

# ---- 填这里 ----
OPENAI_API_KEY="${OPENAI_API_KEY:-sk-你的-deepseek-密钥}"
OPENAI_PROXY_URL="${OPENAI_PROXY_URL:-https://api.deepseek.com/v1}"
DEFAULT_MODEL="${DEFAULT_MODEL:-deepseek-chat}"
PORT="${PORT:-3210}"

# 自动检测 docker
if command -v docker >/dev/null 2>&1; then
  echo "[1/2] 检测到 Docker, 用 docker 一键起..."
  docker rm -f lobechat 2>/dev/null || true
  docker run -d --name lobechat \
    -p ${PORT}:3210 \
    -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
    -e OPENAI_PROXY_URL="${OPENAI_PROXY_URL}" \
    -e DEFAULT_AGENT_CONFIG="${DEFAULT_MODEL}" \
    -e ACCESS_CODE="" \
    lobehub/lobe-chat:latest
  echo "[2/2] LobeChat 已启动: http://localhost:${PORT}"
  echo "  造价通的「AI 助手」标签页将自动加载此地址"
  echo ""
  echo "  日志: docker logs -f lobechat"
  echo "  停止: docker stop lobechat"
  echo "  升级: docker pull lobehub/lobe-chat:latest && docker rm -f lobechat && bash $0"
  exit 0
fi

# 无 docker, 用 Node 自部署
if ! command -v pnpm >/dev/null 2>&1; then
  echo "未检测到 Docker 或 pnpm。请先安装 Docker Desktop(推荐) 或 npm install -g pnpm"
  exit 1
fi

LOBE_DIR="${LOBE_DIR:-$HOME/lobe-chat}"
if [ ! -d "$LOBE_DIR" ]; then
  echo "首次运行,克隆 LobeChat..."
  git clone --depth=1 https://github.com/lobehub/lobe-chat "$LOBE_DIR"
fi
cd "$LOBE_DIR"
git pull --rebase
pnpm install
echo "启动 LobeChat dev 服务..."
OPENAI_API_KEY="${OPENAI_API_KEY}" \
OPENAI_PROXY_URL="${OPENAI_PROXY_URL}" \
DEFAULT_AGENT_CONFIG="${DEFAULT_MODEL}" \
pnpm dev
