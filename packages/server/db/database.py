"""
造价通 - 数据库引擎与 Session
SQLite 默认 + PostgreSQL 可选，同一份 ORM 模型
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# 数据库 URL（环境变量优先）
DB_URL = os.environ.get(
    "COSTPILOT_DB_URL",
    f"sqlite:///{Path(__file__).parent.parent.parent.parent / 'data' / 'sqlite' / '造价通.db'}"
)

# SQLite 需要 check_same_thread=False（FastAPI 多线程访问）
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
