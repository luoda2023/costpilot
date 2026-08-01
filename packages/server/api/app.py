"""工程助手 - FastAPI 主入口

设计原则:
- 最小启动: 只加载核心路由(health/prices/fees/templates)，非核心路由后台懒加载
- 快速启动: on_startup 只做最低限度初始化，数据库备份等放后台线程
- 容错: 所有 import 都有 try/except，任一模块缺失不影响服务器启动
"""
import sys
import os
import threading
import time
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from packages.server.db.database import init_db, engine, backup_db
from packages.server.utils.logger import logger, setup_request_logging

# ============================================================
# 核心路由 — 模块级加载（启动时必须可用，轻量无依赖）
# ============================================================
from packages.server.api.health import router as health_router
from packages.server.api.prices import router as prices_router
from packages.server.api.fees import router as fees_router
from packages.server.api.templates import router as templates_router

app = FastAPI(
	title="工程助手 API",
	description="工程助手 - 工程造价智能辅助系统",
	version="0.2.6",
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


def _register_lazy_routes():
	"""后台线程：延迟注册非核心路由，不阻塞服务器启动

	服务器启动后约 0.5 秒开始注册，注册完即可用。
	任一模块缺失只跳过该路由，不影响整体。
	"""
	import importlib

	time.sleep(0.5)  # 先让服务器开始监听

	lazy_routes = [
		("packages.server.api.projects", "router", "/api/v1/projects", ["项目"]),
		("packages.server.api.chat", "router", "/api/v1/chat", ["AI 聊天"]),
		("packages.server.api.files", "router", "/api/v1/files", ["文件浏览"]),
		("packages.server.api.files", "preview_router", "/api/v1/preview", ["文件预览"]),
		("packages.server.api.ai_config", "router", "/api/v1/ai", ["AI 配置"]),
		("packages.server.api.ai_custom", "router", "/api/v1/ai/custom-configs", ["自定义 AI 配置"]),
		("packages.server.api.quotes", "router", "/api/v1/quotes", ["报价生成"]),
		("packages.server.api.ai_match", "router", "/api/v1/quotes", ["报价生成"]),
		("packages.server.api.ai_assist", "router", "/api/v1/ai", ["AI 智能辅助"]),
		("packages.server.api.knowledge", "router", "/api/v1/kb", ["知识库 RAG"]),
	]

	for mod_path, attr, prefix, tags in lazy_routes:
		try:
			mod = importlib.import_module(mod_path)
			router = getattr(mod, attr, None)
			if router:
				app.include_router(router, prefix=prefix, tags=tags)
				logger.info("✅ 懒加载路由: %s → %s", mod_path, prefix)
		except Exception as e:
			logger.warning("⚠️ 懒加载路由跳过 %s: %s", mod_path, e)


@app.on_event("startup")
def on_startup():
	"""启动时快速初始化 — 不阻塞监听，耗时操作放后台线程"""
	# 1. 初始化数据库表（轻量操作，仅建表）
	try:
		init_db()
		with engine.connect() as conn:
			conn.execute(text("SELECT 1"))
		logger.info("✅ 数据库连接正常")
	except Exception as e:
		logger.critical("❌ 数据库连接失败: %s", e, exc_info=True)

	# 2. 后台线程：注册非核心路由
	t = threading.Thread(target=_register_lazy_routes, daemon=True)
	t.start()

	# 3. 后台线程：数据库备份（每天首次）
	def _backup_worker():
		time.sleep(2)  # 等服务器完全就绪
		try:
			backup_path = backup_db()
			logger.info("✅ 数据库备份完成: %s", backup_path)
		except Exception as e:
			logger.warning("⚠️ 数据库备份失败(非致命): %s", e)
	threading.Thread(target=_backup_worker, daemon=True).start()

	# 4. 输出启动信息（简短）
	import platform
	logger.info("=" * 50)
	logger.info("🚀 工程助手 API 启动成功")
	logger.info("  版本: %s", "0.2.6")
	logger.info("  系统: %s %s", platform.system(), platform.release())
	logger.info("  端口: 8765")
	logger.info("  非核心路由: 后台加载中...")
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
# 核心路由注册（模块级加载，启动即可用）
# ============================================================
app.include_router(health_router, prefix="/health", tags=["健康检查"])
app.include_router(prices_router, prefix="/api/v1/prices", tags=["价格库"])
app.include_router(fees_router, prefix="/api/v1/fees", tags=["费率"])
app.include_router(templates_router, prefix="/api/v1/templates", tags=["模板"])

# ============================================================
# 非核心路由 — 后台线程懒加载（启动后 ~0.5s 注册）
# 包括: projects, chat, files, ai_config, ai_custom, quotes,
#       ai_match, ai_assist, knowledge
# 在 _register_lazy_routes() 中统一注册
# ============================================================


@app.get("/api/status")
def api_status():
	 """纯 API 信息端点"""
	 import platform
	 return {
	 "name": "工程助手 API",
	 "version": "0.2.6",
	 "system": f"{platform.system()} {platform.release()}",
	 "python": sys.version.split()[0],
	 "docs": "/docs",
	 "redoc": "/redoc",
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