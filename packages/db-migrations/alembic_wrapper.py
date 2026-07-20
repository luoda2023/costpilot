"""Alembic 配置 - 造价通"""
from alembic.context import config
import os
import sys
from pathlib import Path

# 让 alembic 能找到本项目的 db 包
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from packages.server.db.database import DB_URL, engine
from packages.server.db.models import Base

target_metadata = Base.metadata


def run_migrations_offline():
    from alembic import context
    context.configure(url=DB_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    from alembic import context
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


def main():
    from alembic import context
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


# Alembic env.py 调用入口
if __name__ == "__main__":
    main()
