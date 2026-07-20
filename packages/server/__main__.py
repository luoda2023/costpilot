"""
造价通 - 后端入口 (PyInstaller 打包目标)

打包后:
  costpilot-server.exe  ← 直接双击运行,起 uvicorn
  costpilot-server.exe --port 8765 --host 127.0.0.1
"""
import sys
import os

# PyInstaller 打包后, 数据库 / config.yaml 放在 sys._MEIPASS 或可执行文件同目录
def _setup_paths():
    if getattr(sys, "_MEIPASS", None):
        # PyInstaller onefile 解压到 _MEIPASS, 但写文件要去 exe 同目录
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 把项目根加到 sys.path 让 import packages.* 能跑
    if base not in sys.path:
        sys.path.insert(0, base)
    # 切到工程根, alembic / config.yaml 路径才正确
    os.chdir(base)
    return base

_setup_paths()

import argparse
import uvicorn

def main():
    parser = argparse.ArgumentParser(description="造价通 后端服务")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"造价通后端启动: http://{args.host}:{args.port}")
    uvicorn.run(
        "packages.server.api.app:app",
        host=args.host,
        port=args.port,
        log_level="info",
        reload=False,
    )

if __name__ == "__main__":
    main()
