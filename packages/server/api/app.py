"""工程助手 - FastAPI 主入口"""
import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from packages.server.db.database import init_db, engine, backup_db
from packages.server.utils.logger import logger, setup_request_logging

# 显式导入 router(避免子模块导入失败)
from packages.server.api.health import router as health_router
from packages.server.api.prices import router as prices_router
from packages.server.api.fees import router as fees_router
from packages.server.api.templates import router as templates_router
from packages.server.api.projects import router as projects_router
from packages.server.api.chat import router as chat_router
from packages.server.api.files import router as files_router

app = FastAPI(
	title="工程助手 API",
	description="工程助手 - 工程造价智能辅助系统",
    version="0.2.4",
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

# 请求日志
setup_request_logging(app)


@app.on_event("startup")
def on_startup():
    """启动时执行环境检查"""
    # 1. 检查数据库
    try:
        init_db()
        # 验证连接是否可用
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ 数据库连接正常")
    except Exception as e:
        logger.critical("❌ 数据库连接失败: %s", e, exc_info=True)
        print(f"[FATAL] 数据库连接失败: {e}")
        print("[FATAL] 请确保已安装 SQLite 或配置正确的数据库路径")

    # 1b. 数据库备份(每天首次启动自动备份)
    try:
        backup_path = backup_db()
        logger.info("✅ 数据库备份完成: %s", backup_path)
    except Exception as e:
        logger.warning("⚠️ 数据库备份失败(非致命): %s", e)

    # 2. 检查配置文件
    config_path = Path(__file__).resolve().parent.parent.parent.parent / "config.yaml"
    if config_path.exists():
        logger.info("✅ 配置文件存在: %s", config_path)
    else:
        logger.warning("⚠️ 配置文件不存在: %s", config_path)

    # 3. 检查前端静态文件
    static_path = _static_dir()
    if static_path.exists():
        logger.info("✅ 前端静态文件已就绪: %s", static_path)
    else:
        logger.warning("⚠️ 前端静态文件未构建: %s", static_path)

    # 4. 检查日志目录
    from packages.server.utils.logger import LOG_DIR
    logger.info("✅ 日志目录: %s", LOG_DIR)

# 5. 输出启动信息
    import platform
    logger.info("=" * 50)
    logger.info("🚀 工程助手 API 启动成功")
    logger.info("  版本: %s", "0.2.4")
    logger.info("  系统: %s %s", platform.system(), platform.release())
    logger.info("  Python: %s", sys.version.split()[0])
    logger.info("  文档: http://127.0.0.1:8765/docs")
    logger.info("=" * 50)


@app.on_event("shutdown")
def on_shutdown():
    """关闭时释放资源，防止内存泄漏"""
    try:
        # 关闭数据库连接池
        from packages.server.db.database import engine
        engine.dispose()
        logger.info("✅ 数据库连接池已释放")
    except Exception as e:
        logger.warning("⚠️ 数据库释放失败: %s", e)

    try:
        # 释放 AI 客户端 Session（关闭连接池）
        from packages.server.ai.client import reset_ai_client
        from packages.server.ai.image_client import reset_image_client
        reset_ai_client()
        reset_image_client()
        logger.info("✅ AI 客户端连接已释放")
    except Exception as e:
        logger.warning("⚠️ AI 客户端释放失败: %s", e)


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

# AI 智能导入匹配
from packages.server.api.ai_match import router as ai_match_router
app.include_router(ai_match_router, prefix="/api/v1/quotes", tags=["报价生成"])

# AI 智能辅助(parse-table / fill-fields / parse-project)
from packages.server.api.ai_assist import router as ai_assist_router
app.include_router(ai_assist_router, prefix="/api/v1/ai", tags=["AI 智能辅助"])

# 知识库 RAG
from packages.server.api.knowledge import router as knowledge_router
app.include_router(knowledge_router, prefix="/api/v1/kb", tags=["知识库 RAG"])


@app.get("/api/status")
def api_status():
 """纯 API 信息端点"""
 from packages.server.utils.logger import LOG_DIR
 import platform
 return {
 "name": "工程助手 API",
 "version": "0.1.0",
 "system": f"{platform.system()} {platform.release()}",
 "python": sys.version.split()[0],
 "docs": "/docs",
 "redoc": "/redoc",
 "log_dir": str(LOG_DIR),
 "static_files": str(_static_dir()) if _static_dir().exists() else "未构建",
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