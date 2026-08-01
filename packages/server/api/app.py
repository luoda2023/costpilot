"""工程助手 - FastAPI 主入口

设计原则:
- 同步注册所有路由（确保 StaticFiles mount 在最后，不拦截 API 请求）
- 所有 import 都有 try/except 容错，任一模块缺失跳过该路由
- 耗时操作(数据库备份)放后台线程，不阻塞启动
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
# 路由导入 — 全部 try/except 容错，任一模块缺失跳过
# 同步加载（约耗时 2s），确保 mount 之前所有路由都注册好
# ============================================================
from packages.server.api.health import router as health_router
from packages.server.api.prices import router as prices_router
from packages.server.api.fees import router as fees_router
from packages.server.api.templates import router as templates_router

app = FastAPI(
	title="工程助手 API",
	description="工程助手 - 工程造价智能辅助系统",
	version="0.2.7",
	docs_url="/docs",
	redoc_url="/redoc",
)

# CORS
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
	"""启动时初始化 — 建表轻量操作，备份放后台"""
	# 1. 建表 + 验证连接
	try:
		init_db()
		with engine.connect() as conn:
			conn.execute(text("SELECT 1"))
		logger.info("✅ 数据库连接正常")
	except Exception as e:
		logger.critical("❌ 数据库连接失败: %s", e, exc_info=True)

	# 2. 数据库备份（每天首次，后台线程不阻塞）
	def _backup_worker():
		try:
			backup_path = backup_db()
			logger.info("✅ 数据库备份完成: %s", backup_path)
		except Exception as e:
			logger.warning("⚠️ 数据库备份失败(非致命): %s", e)
	threading.Thread(target=_backup_worker, daemon=True).start()

	# 3. 启动信息
	import platform
	logger.info("=" * 50)
	logger.info("🚀 工程助手 API 启动成功 v%s", "0.2.7")
	logger.info("  系统: %s %s", platform.system(), platform.release())
	logger.info("  端口: 8765")
	logger.info("=" * 50)


@app.on_event("shutdown")
def on_shutdown():
	"""关闭时释放资源"""
	try:
		engine.dispose()
		logger.info("✅ 数据库连接池已释放")
	except Exception as e:
		logger.warning("⚠️ 数据库释放失败: %s", e)
	try:
		from packages.server.ai.client import reset_ai_client
		from packages.server.ai.image_client import reset_image_client
		reset_ai_client()
		reset_image_client()
		logger.info("✅ AI 客户端连接已释放")
	except Exception as e:
		logger.warning("⚠️ AI 客户端释放失败: %s", e)


# ============================================================
# 路由注册 — 全部在 mount 之前完成
# ============================================================
app.include_router(health_router, prefix="/health", tags=["健康检查"])
app.include_router(prices_router, prefix="/api/v1/prices", tags=["价格库"])
app.include_router(fees_router, prefix="/api/v1/fees", tags=["费率"])
app.include_router(templates_router, prefix="/api/v1/templates", tags=["模板"])

# 项目
try:
	from packages.server.api.projects import router as projects_router
	app.include_router(projects_router, prefix="/api/v1/projects", tags=["项目"])
	logger.info("✅ 路由: projects")
except Exception as e:
	logger.warning("⚠️ 路由跳过 projects: %s", e)

# AI 聊天
try:
	from packages.server.api.chat import router as chat_router
	app.include_router(chat_router, prefix="/api/v1/chat", tags=["AI 聊天"])
	logger.info("✅ 路由: chat")
except Exception as e:
	logger.warning("⚠️ 路由跳过 chat: %s", e)

# 文件浏览
try:
	from packages.server.api.files import router as files_router
	app.include_router(files_router, prefix="/api/v1/files", tags=["文件浏览"])
	logger.info("✅ 路由: files")
except Exception as e:
	logger.warning("⚠️ 路由跳过 files: %s", e)

# 文件预览
try:
	from packages.server.api.files import preview_router as files_preview_router
	app.include_router(files_preview_router, prefix="/api/v1/preview", tags=["文件预览"])
	logger.info("✅ 路由: preview")
except Exception as e:
	logger.warning("⚠️ 路由跳过 preview: %s", e)

# AI 配置管理
try:
	from packages.server.api.ai_config import router as ai_config_router
	app.include_router(ai_config_router, prefix="/api/v1/ai", tags=["AI 配置"])
	logger.info("✅ 路由: ai_config")
except Exception as e:
	logger.warning("⚠️ 路由跳过 ai_config: %s", e)

# 自定义 AI 配置
try:
	from packages.server.api.ai_custom import router as ai_custom_router
	app.include_router(ai_custom_router, prefix="/api/v1/ai/custom-configs", tags=["自定义 AI 配置"])
	logger.info("✅ 路由: ai_custom")
except Exception as e:
	logger.warning("⚠️ 路由跳过 ai_custom: %s", e)

# 报价生成
try:
	from packages.server.api.quotes import router as quotes_router
	app.include_router(quotes_router, prefix="/api/v1/quotes", tags=["报价生成"])
	logger.info("✅ 路由: quotes")
except Exception as e:
	logger.warning("⚠️ 路由跳过 quotes: %s", e)

# AI 智能导入匹配
try:
	from packages.server.api.ai_match import router as ai_match_router
	app.include_router(ai_match_router, prefix="/api/v1/quotes", tags=["报价生成"])
	logger.info("✅ 路由: ai_match")
except Exception as e:
	logger.warning("⚠️ 路由跳过 ai_match: %s", e)

# AI 智能辅助
try:
	from packages.server.api.ai_assist import router as ai_assist_router
	app.include_router(ai_assist_router, prefix="/api/v1/ai", tags=["AI 智能辅助"])
	logger.info("✅ 路由: ai_assist")
except Exception as e:
	logger.warning("⚠️ 路由跳过 ai_assist: %s", e)

# 知识库 RAG
try:
	from packages.server.api.knowledge import router as knowledge_router
	app.include_router(knowledge_router, prefix="/api/v1/kb", tags=["知识库 RAG"])
	logger.info("✅ 路由: knowledge")
except Exception as e:
	logger.warning("⚠️ 路由跳过 knowledge: %s", e)


@app.get("/api/status")
def api_status():
	import platform
	return {
		"name": "工程助手 API",
		"version": "0.2.7",
		"system": f"{platform.system()} {platform.release()}",
		"python": sys.version.split()[0],
		"docs": "/docs",
		"redoc": "/redoc",
	}


# ============================================================
# 最后: 挂载前端静态文件
# ⚠️ 所有 API 路由必须在 mount 之前注册，否则 StaticFiles
#  catch-all 会拦截 API 请求返回 405
# ============================================================
def _static_dir() -> Path:
	if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
		base = Path(sys.executable).resolve().parent
		return base / "web" / "dist"
	else:
		return Path(__file__).resolve().parent.parent.parent.parent / "apps" / "web" / "dist"


static_path = _static_dir()
if static_path.exists():
	app.mount("/", StaticFiles(directory=str(static_path), html=True), name="frontend")
	print(f"[app] 前端静态文件已挂载: {static_path}")
else:
	print(f"[app] 前端静态目录不存在(开发模式正常): {static_path}")