"""
工程助手 - 数据库引擎与 Session
SQLite 默认 + PostgreSQL 可选，同一份 ORM 模型
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from packages.server.utils.logger import logger

def _db_path() -> Path:
    """数据库文件路径

    ⚠ 卸载重装不丢数据的关键:
      ① 优先使用 ENGINEERING_ASSISTANT_DATA_DIR 环境变量(由 Electron 主进程设置)
      ② 打包后: exe 同目录/data/sqlite(旧版兼容)
      ③ 开发模式: 项目根/data/sqlite
    """
    data_dir = os.environ.get("ENGINEERING_ASSISTANT_DATA_DIR")
    if data_dir:
        return Path(data_dir) / "data" / "sqlite" / "工程助手.db"

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).parent.parent.parent.parent
    return base / 'data' / 'sqlite' / '工程助手.db'

# 数据库 URL (环境变量优先)
DB_URL = os.environ.get(
    "ENGINEERING_ASSISTANT_DB_URL",
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


def backup_db(max_backups: int = 10) -> Path:
 """备份当前数据库文件到 data/sqlite/backups/

 自动清理超出 max_backups 的旧备份。
 返回备份文件路径。
 """
 import shutil
 from datetime import datetime

 db_file = _db_path()
 if not db_file.exists():
  logger.warning("数据库文件不存在，跳过备份: %s", db_file)
  return db_file

 backup_dir = db_file.parent / "backups"
 backup_dir.mkdir(parents=True, exist_ok=True)

 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
 backup_path = backup_dir / f"工程助手_{timestamp}.db"

 shutil.copy2(db_file, backup_path)
 logger.info("数据库已备份: %s (%d bytes)", backup_path, backup_path.stat().st_size)

 # 清理旧备份：保留最近 max_backups 个
 backups = sorted(backup_dir.glob("工程助手_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
 for old in backups[max_backups:]:
  old.unlink()
  logger.info("清理旧备份: %s", old)

 return backup_path
