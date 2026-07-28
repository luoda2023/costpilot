"""
工程助手 - 日志配置

用法:
  from packages.server.utils.logger import logger
  logger.info("服务启动")
  logger.error("出错了", exc_info=True)
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# 日志目录: 运行目录下的 logs/
LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志格式
_FORMAT = "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

# 控制台 handler
_console = logging.StreamHandler(sys.stdout)
_console.setLevel(logging.DEBUG)
_console.setFormatter(logging.Formatter(_FORMAT, _DATE_FMT))

# 文件 handler (按大小轮转, 每 10MB, 保留 5 个)
_file = RotatingFileHandler(
    LOG_DIR / "app.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
_file.setLevel(logging.INFO)
_file.setFormatter(logging.Formatter(_FORMAT, _DATE_FMT))


def get_logger(name: str = "costpilot") -> logging.Logger:
    """获取或创建 logger"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(_console)
        logger.addHandler(_file)
    return logger


# 默认 logger
logger = get_logger()


def setup_request_logging(app) -> None:
    """为 FastAPI 应用添加请求日志中间件"""
    from fastapi import Request
    from starlette.middleware.base import BaseHTTPMiddleware
    import time

    class RequestLogMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            start = time.time()
            response = await call_next(request)
            cost = (time.time() - start) * 1000
            logger.info(
                "%s %s → %s (%.0fms)",
                request.method,
                request.url.path,
                response.status_code,
                cost,
            )
            return response

    app.add_middleware(RequestLogMiddleware)