"""
造价通 - 数据库 ORM 模型
14 张表，SQLite + PostgreSQL 双 schema 兼容
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean,
    ForeignKey, Index, JSON, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ============================================================================
# 价格库 5 张表
# ============================================================================

class Specialty(Base):
    """8 大专业"""
    __tablename__ = "t_specialty"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True, comment="专业名")
    code = Column(String(16), nullable=False, unique=True, comment="专业代码: 土建/市政/机电安装/...")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class PriceUnit(Base):
    """17,944 条综合单价"""
    __tablename__ = "t_price_unit"
    id = Column(Integer, primary_key=True, autoincrement=True)
    specialty_id = Column(Integer, ForeignKey("t_specialty.id"), nullable=False, index=True)
    item_name = Column(String(256), nullable=False, index=True, comment="项目名称")
    unit = Column(String(32), nullable=False, comment="单位: m²/m³/t/...")
    price = Column(String(64), nullable=False, comment="综合单价(字符串保留原值,可能含组分)")
    region = Column(String(64), default="全国", index=True, comment="适用地区")
    calc_rule = Column(Text, comment="计量规则")
    remark = Column(Text, comment="备注")
    source_file = Column(String(256), nullable=False, comment="来源文件名")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_price_unit_name_region", "item_name", "region"),
    )


class TopicPrice(Base):
    """370 条市政专题(管道/基坑/钢板桩/降水/桩基)"""
    __tablename__ = "t_topic_price"
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(32), nullable=False, index=True, comment="专题: 管道铺设与修复/深基坑开挖与支护/钢板桩/降水工程/桩基与地基处理")
    item_name = Column(String(256), nullable=False, index=True)
    unit = Column(String(32), nullable=False)
    price = Column(String(64), nullable=False)
    calc_rule = Column(Text)
    remark = Column(Text)
    source_file = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RegionInfoPrice(Base):
    """7 省市信息价(M5 扩到 36+)"""
    __tablename__ = "t_region_info_price"
    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String(64), nullable=False, index=True, comment="省/市")
    period = Column(String(16), nullable=False, comment="期间(年月), 如 2025-03")
    item_name = Column(String(256), nullable=False, index=True)
    unit = Column(String(32), nullable=False)
    price = Column(Float, nullable=False)
    source_file = Column(String(256))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_region_period_item", "region", "period", "item_name"),
    )


class FeeRate(Base):
    """规费/措施费/税金费率"""
    __tablename__ = "t_fee_rate"
    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String(64), nullable=False, index=True, comment="地区")
    fee_type = Column(String(32), nullable=False, comment="规费/措施费/税金")
    fee_subitem = Column(String(64), comment="子项: 社保/公积金/安全文明/夜间施工...")
    rate = Column(Float, nullable=False, comment="费率(小数: 0.2183)")
    calc_base = Column(String(64), comment="计算基数: 人工费/分部分项+措施+其他")
    remark = Column(Text)
    source_file = Column(String(256))
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# 项目库 3 张表
# ============================================================================

class Project(Base):
    """项目档案"""
    __tablename__ = "t_project"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, comment="项目名称")
    region = Column(String(64), nullable=False, index=True, comment="项目所在地")
    stage = Column(String(16), nullable=False, comment="估算/概算/预算/结算")
    owner_id = Column(Integer, ForeignKey("t_user.id"), comment="负责人")
    status = Column(String(16), default="草稿", comment="草稿/进行中/已交付/已归档")
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Quantity(Base):
    """工程量表"""
    __tablename__ = "t_quantity"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("t_project.id"), nullable=False, index=True)
    specialty_id = Column(Integer, ForeignKey("t_specialty.id"), index=True)
    item_name = Column(String(256), nullable=False, comment="项目名称")
    unit = Column(String(32), nullable=False)
    qty = Column(Float, nullable=False, comment="工程量")
    matched_price_id = Column(Integer, ForeignKey("t_price_unit.id"), comment="匹配到的价格库ID")
    custom_price = Column(Float, comment="自定义单价(覆盖匹配价)")
    remark = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Quote(Base):
    """报价单(汇总)"""
    __tablename__ = "t_quote"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("t_project.id"), nullable=False, index=True)
    version = Column(Integer, default=1, comment="版本号")
    total = Column(Float, nullable=False, default=0)
    category1 = Column(Float, default=0, comment="一类: 分部分项")
    category2 = Column(Float, default=0, comment="二类: 措施费")
    category3 = Column(Float, default=0, comment="三类: 规费")
    tax = Column(Float, default=0, comment="税金")
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# 模板库 3 张表
# ============================================================================

class TemplateType(Base):
    """8 类文本格式谱"""
    __tablename__ = "t_template_type"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True, comment="类型名: 可研报告/施组/...")
    doc_type = Column(String(16), comment="文档类型: report/manual/contract/...")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Template(Base):
    """模板内容"""
    __tablename__ = "t_template"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type_id = Column(Integer, ForeignKey("t_template_type.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    content_md = Column(Text, nullable=False, comment="Markdown 模板")
    yaml_skeleton = Column(Text, comment="YAML 章节骨架")
    version = Column(String(16), default="1.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TemplateField(Base):
    """模板字段定义"""
    __tablename__ = "t_template_field"
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("t_template.id"), nullable=False, index=True)
    field_key = Column(String(64), nullable=False, comment="字段键: project_name/region/...")
    field_label = Column(String(128), nullable=False, comment="字段中文标签")
    field_type = Column(String(16), default="text", comment="text/number/date/select/richtext")
    required = Column(Boolean, default=False)
    default_value = Column(Text)
    options = Column(JSON, comment="select 类型的可选值")


# ============================================================================
# AI 3 张表
# ============================================================================

class ChatSession(Base):
    """聊天会话"""
    __tablename__ = "t_chat_session"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("t_project.id"), index=True)
    title = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    """聊天消息"""
    __tablename__ = "t_chat_message"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("t_chat_session.id"), nullable=False, index=True)
    role = Column(String(16), nullable=False, comment="user/assistant/system/tool")
    content = Column(Text, nullable=False)
    tool_calls = Column(JSON, comment="工具调用记录")
    tool_call_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeChunk(Base):
    """知识库分块(PDF/规范/案例等向量化文本)"""
    __tablename__ = "t_knowledge_chunk"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_file = Column(String(256), nullable=False, index=True, comment="来源文件")
    page = Column(Integer, comment="页码")
    chunk_text = Column(Text, nullable=False)
    embedding_id = Column(String(64), comment="ChromaDB 中的向量ID")
    extra_metadata = Column(JSON, name="metadata")
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# 协同与开放 v1.1 新增 3 张表
# ============================================================================

class User(Base):
    """用户"""
    __tablename__ = "t_user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, unique=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(16), default="user", comment="admin/user/viewer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """审计日志"""
    __tablename__ = "t_audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("t_user.id"), index=True)
    action = Column(String(32), nullable=False, index=True, comment="create/update/delete/login/export")
    target = Column(String(64), comment="操作对象: 项目/价格/模板/...")
    payload = Column(JSON, comment="操作数据快照")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_audit_user_time", "user_id", "created_at"),
    )


class ApiToken(Base):
    """API Token (M6 开放接口)"""
    __tablename__ = "t_api_token"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("t_user.id"), nullable=False, index=True)
    token = Column(String(128), nullable=False, unique=True)
    scope = Column(String(128), comment="权限范围: price:read,doc:write,...")
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
