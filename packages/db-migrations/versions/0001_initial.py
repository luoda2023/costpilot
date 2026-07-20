"""${message}

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(name):
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    return insp.has_table(name)


def upgrade():
    # 价格库 5 张表
    if not _has_table("t_specialty"):
        op.create_table(
            "t_specialty",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(64), nullable=False, unique=True),
            sa.Column("code", sa.String(16), nullable=False, unique=True),
            sa.Column("description", sa.Text),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    if not _has_table("t_price_unit"):
        op.create_table(
            "t_price_unit",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("specialty_id", sa.Integer, sa.ForeignKey("t_specialty.id"), nullable=False),
            sa.Column("item_name", sa.String(256), nullable=False, index=True),
            sa.Column("unit", sa.String(32), nullable=False),
            sa.Column("price", sa.String(64), nullable=False, comment="综合单价(字符串保留原值)"),
            sa.Column("region", sa.String(64), default="全国", index=True),
            sa.Column("calc_rule", sa.Text),
            sa.Column("remark", sa.Text),
            sa.Column("source_file", sa.String(256), nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )
        op.create_index("idx_price_unit_name_region", "t_price_unit", ["item_name", "region"])

    if not _has_table("t_topic_price"):
        op.create_table(
            "t_topic_price",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("topic", sa.String(32), nullable=False, index=True),
            sa.Column("item_name", sa.String(256), nullable=False, index=True),
            sa.Column("unit", sa.String(32), nullable=False),
            sa.Column("price", sa.String(64), nullable=False),
            sa.Column("calc_rule", sa.Text),
            sa.Column("remark", sa.Text),
            sa.Column("source_file", sa.String(256), nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    if not _has_table("t_region_info_price"):
        op.create_table(
            "t_region_info_price",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("region", sa.String(64), nullable=False, index=True),
            sa.Column("period", sa.String(16), nullable=False),
            sa.Column("item_name", sa.String(256), nullable=False, index=True),
            sa.Column("unit", sa.String(32), nullable=False),
            sa.Column("price", sa.Float, nullable=False),
            sa.Column("source_file", sa.String(256)),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )
        op.create_index("idx_region_period_item", "t_region_info_price", ["region", "period", "item_name"])

    if not _has_table("t_fee_rate"):
        op.create_table(
            "t_fee_rate",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("region", sa.String(64), nullable=False, index=True),
            sa.Column("fee_type", sa.String(32), nullable=False),
            sa.Column("fee_subitem", sa.String(64)),
            sa.Column("rate", sa.Float, nullable=False),
            sa.Column("calc_base", sa.String(64)),
            sa.Column("remark", sa.Text),
            sa.Column("source_file", sa.String(256)),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    # 协同与开放 - 用户先建(被引用)
    if not _has_table("t_user"):
        op.create_table(
            "t_user",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("username", sa.String(64), nullable=False, unique=True),
            sa.Column("password_hash", sa.String(256), nullable=False),
            sa.Column("role", sa.String(16), default="user"),
            sa.Column("is_active", sa.Boolean, default=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    # 项目库 3 张表
    if not _has_table("t_project"):
        op.create_table(
            "t_project",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("region", sa.String(64), nullable=False, index=True),
            sa.Column("stage", sa.String(16), nullable=False),
            sa.Column("owner_id", sa.Integer, sa.ForeignKey("t_user.id")),
            sa.Column("status", sa.String(16), default="草稿"),
            sa.Column("note", sa.Text),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        )

    if not _has_table("t_quantity"):
        op.create_table(
            "t_quantity",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("project_id", sa.Integer, sa.ForeignKey("t_project.id"), nullable=False, index=True),
            sa.Column("specialty_id", sa.Integer, sa.ForeignKey("t_specialty.id"), index=True),
            sa.Column("item_name", sa.String(256), nullable=False),
            sa.Column("unit", sa.String(32), nullable=False),
            sa.Column("qty", sa.Float, nullable=False),
            sa.Column("matched_price_id", sa.Integer, sa.ForeignKey("t_price_unit.id")),
            sa.Column("custom_price", sa.Float),
            sa.Column("remark", sa.Text),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    if not _has_table("t_quote"):
        op.create_table(
            "t_quote",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("project_id", sa.Integer, sa.ForeignKey("t_project.id"), nullable=False, index=True),
            sa.Column("version", sa.Integer, default=1),
            sa.Column("total", sa.Float, nullable=False, default=0),
            sa.Column("category1", sa.Float, default=0),
            sa.Column("category2", sa.Float, default=0),
            sa.Column("category3", sa.Float, default=0),
            sa.Column("tax", sa.Float, default=0),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    # 模板库 3 张表
    if not _has_table("t_template_type"):
        op.create_table(
            "t_template_type",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(64), nullable=False, unique=True),
            sa.Column("doc_type", sa.String(16)),
            sa.Column("description", sa.Text),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    if not _has_table("t_template"):
        op.create_table(
            "t_template",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("type_id", sa.Integer, sa.ForeignKey("t_template_type.id"), nullable=False, index=True),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("content_md", sa.Text, nullable=False),
            sa.Column("yaml_skeleton", sa.Text),
            sa.Column("version", sa.String(16), default="1.0"),
            sa.Column("is_active", sa.Boolean, default=True),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        )

    if not _has_table("t_template_field"):
        op.create_table(
            "t_template_field",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("template_id", sa.Integer, sa.ForeignKey("t_template.id"), nullable=False, index=True),
            sa.Column("field_key", sa.String(64), nullable=False),
            sa.Column("field_label", sa.String(128), nullable=False),
            sa.Column("field_type", sa.String(16), default="text"),
            sa.Column("required", sa.Boolean, default=False),
            sa.Column("default_value", sa.Text),
            sa.Column("options", sa.JSON),
        )

    # AI 3 张表
    if not _has_table("t_chat_session"):
        op.create_table(
            "t_chat_session",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("project_id", sa.Integer, sa.ForeignKey("t_project.id"), index=True),
            sa.Column("title", sa.String(128)),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    if not _has_table("t_chat_message"):
        op.create_table(
            "t_chat_message",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("session_id", sa.Integer, sa.ForeignKey("t_chat_session.id"), nullable=False, index=True),
            sa.Column("role", sa.String(16), nullable=False),
            sa.Column("content", sa.Text, nullable=False),
            sa.Column("tool_calls", sa.JSON),
            sa.Column("tool_call_id", sa.String(64)),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    if not _has_table("t_knowledge_chunk"):
        op.create_table(
            "t_knowledge_chunk",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("source_file", sa.String(256), nullable=False, index=True),
            sa.Column("page", sa.Integer),
            sa.Column("chunk_text", sa.Text, nullable=False),
            sa.Column("embedding_id", sa.String(64)),
 sa.Column("metadata", sa.JSON),
 sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
 )

    # 协同与开放 余下 2 张表
    if not _has_table("t_audit_log"):
        op.create_table(
            "t_audit_log",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("t_user.id"), index=True),
            sa.Column("action", sa.String(32), nullable=False, index=True),
            sa.Column("target", sa.String(64)),
            sa.Column("payload", sa.JSON),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
        )
        op.create_index("idx_audit_user_time", "t_audit_log", ["user_id", "created_at"])

    if not _has_table("t_api_token"):
        op.create_table(
            "t_api_token",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("t_user.id"), nullable=False, index=True),
            sa.Column("token", sa.String(128), nullable=False, unique=True),
            sa.Column("scope", sa.String(128)),
            sa.Column("expires_at", sa.DateTime),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )


def downgrade():
    for t in [
        "t_api_token", "t_audit_log", "t_knowledge_chunk", "t_chat_message", "t_chat_session",
        "t_template_field", "t_template", "t_template_type",
        "t_quote", "t_quantity", "t_project",
        "t_fee_rate", "t_region_info_price", "t_topic_price", "t_price_unit",
        "t_specialty", "t_user",
    ]:
        op.drop_table(t)
