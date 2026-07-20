"""造价通 - FastAPI 主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/")
def root():
    return {
        "name": "造价通 CostPilot API",
        "version": "0.1.0",
        "docs": "/docs",
    }


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
