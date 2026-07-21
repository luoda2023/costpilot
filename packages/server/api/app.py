"""造价通 - FastAPI 主入口"""
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from packages.server.db.database import init_db

# 显式导入 router(避免子模块导入失败)
from packages.server.api.health import router as health_router
from packages.server.api.prices import router as prices_router
from packages.server.api.fees import router as fees_router
from packages.server.api.templates import router as templates_router
from packages.server.api.projects import router as projects_router
from packages.server.api.chat import router as chat_router
from packages.server.api.files import router as files_router

app = FastAPI(
    title="造价通 CostPilot API",
    description="工程造价智能助手 - 本地 API 服务",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - 桌面端 Electron 渲染进程可访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# ============================================================
# 重要: 所有 API 路由必须在 mount('/') 之前注册!
# Starlette 的 StaticFiles mount 会 catch-all 所有请求,
# 如果 mount 先注册, API 路由永远收不到请求。
# ============================================================

app.include_router(health_router, prefix="/health", tags=["健康检查"])
app.include_router(prices_router, prefix="/api/v1/prices", tags=["价格库"])
app.include_router(fees_router, prefix="/api/v1/fees", tags=["费率"])
app.include_router(templates_router, prefix="/api/v1/templates", tags=["模板"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["项目"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["AI 聊天"])
app.include_router(files_router, prefix="/api/v1/files", tags=["文件浏览"])

# 文件预览(独立路由)
from packages.server.api.files import preview_router as files_preview_router
app.include_router(files_preview_router, prefix="/api/v1/preview", tags=["文件预览"])

# AI 配置管理
from packages.server.api.ai_config import router as ai_config_router
app.include_router(ai_config_router, prefix="/api/v1/ai", tags=["AI 配置"])

# 报价生成
from packages.server.api.quotes import router as quotes_router
app.include_router(quotes_router, prefix="/api/v1/quotes", tags=["报价生成"])

# 知识库 RAG
from packages.server.api.knowledge import router as knowledge_router
app.include_router(knowledge_router, prefix="/api/v1/kb", tags=["知识库 RAG"])


@app.get("/api/status")
def api_status():
    """纯 API 信息端点"""
    return {
        "name": "造价通 CostPilot API",
        "version": "0.1.0",
        "docs": "/docs",
    }


# ============================================================
# 最后: 挂载前端静态文件(生产模式)
# 后端托管前端 SPA, 让 Electron 从 http://127.0.0.1:8765 加载
# 而不是从 file:// 协议加载, 这样 /api 请求同源正常
# ============================================================
def _static_dir() -> Path:
    """打包后: exe 同目录/web/dist; 开发模式: 项目根/apps/web/dist"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller onefile, 静态文件在 exe 旁边
        base = Path(sys.executable).resolve().parent
        return base / "web" / "dist"
    else:
        # 开发模式: packages/server/api/ -> 4 次 parent 到项目根
        return Path(__file__).resolve().parent.parent.parent.parent / "apps" / "web" / "dist"


static_path = _static_dir()
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="frontend")
    print(f"[app] 前端静态文件已挂载: {static_path}")
else:
    print(f"[app] 前端静态目录不存在(开发模式正常): {static_path}")