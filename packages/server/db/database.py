"""
造价通 - 数据库引擎与 Session
SQLite 默认 + PostgreSQL 可选，同一份 ORM 模型
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

def _db_path() -> Path:
    """数据库文件路径

    ⚠ 卸载重装不丢数据的关键:
      ① 优先使用 COSTPILOT_DATA_DIR 环境变量(由 Electron 主进程设置)
      ② 打包后: exe 同目录/data/sqlite(旧版兼容)
      ③ 开发模式: 项目根/data/sqlite
    """
    data_dir = os.environ.get("COSTPILOT_DATA_DIR")
    if data_dir:
        return Path(data_dir) / "data" / "sqlite" / "造价通.db"

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).parent.parent.parent.parent
    return base / 'data' / 'sqlite' / '造价通.db'

# 数据库 URL (环境变量优先)
DB_URL = os.environ.get(
    "COSTPILOT_DB_URL",
    f"sqlite:///{_db_path()}"
)

# SQLite 需要 check_same_thread=False (FastAPI 多线程访问)
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, connect_args=connect_args, echo=False, pool_pre_ping=True)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def get_db():
    """FastAPI 依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """建表（开发期用；生产用 Alembic 迁移）"""
    from .models import Base
    Base.metadata.create_all(bind=engine)


def reset_db():
    """重建所有表（开发期清库用）"""
    from .models import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
