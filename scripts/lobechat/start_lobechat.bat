@echo off
REM 造价通 - Windows 一键启动 LobeChat
REM 需先安装 Docker Desktop(推荐) 或 Node + pnpm

set OPENAI_API_KEY=sk-你的-deepseek-密钥
set OPENAI_PROXY_URL=https://api.deepseek.com/v1
set DEFAULT_MODEL=deepseek-chat
set PORT=3210

where docker >nul 2>nul
if %errorlevel%==0 (
  echo [1/2] 检测到 Docker, 启动LobeChat 容器...
  docker rm -f lobechat 2>nul
  docker run -d --name lobechat ^
    -p %PORT%:3210 ^
    -e OPENAI_API_KEY=%OPENAI_API_KEY% ^
    -e OPENAI_PROXY_URL=%OPENAI_PROXY_URL% ^
    -e DEFAULT_AGENT_CONFIG=%DEFAULT_MODEL% ^
    -e ACCESS_CODE= ^
    lobehub/lobe-chat:latest
  echo [2/2] LobeChat 已启动: http://localhost:%PORT%
  echo   造价通的 AI 助手标签页将自动加载
  echo   日志: docker logs -f lobechat
  exit /b 0
)

echo 未检测到 Docker。请先安装 Docker Desktop for Windows:
echo   https://www.docker.com/products/docker-desktop/
pause
