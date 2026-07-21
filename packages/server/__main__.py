"""
造价通 - 后端入口 (PyInstaller 打包目标)

打包后:
  costpilot-server.exe  ← 直接双击运行,起 uvicorn
  costpilot-server.exe --port 8765 --host 127.0.0.1
"""
import sys
import os
import argparse
import uvicorn


def _setup_paths():
    """确保 Python 能找到 packages.* 模块"""
    if getattr(sys, "frozen", False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller onefile: 工作目录为 exe 所在目录
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if base not in sys.path:
        sys.path.insert(0, base)
    os.chdir(base)
    return base


_setup_paths()

# 直接 import app 对象 (不用字符串传参, 避免 PyInstaller frozen 环境模块解析问题)
from packages.server.api.app import app


def main():
    parser = argparse.ArgumentParser(description="造价通 后端服务")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"造价通后端启动: http://{args.host}:{args.port}")
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()