"""AI 聊天 API

设计:
  - 不自训练模型, 走外部在线 API(OpenAI 兼容,5 大主流可切)
  - 强制 RAG 先行: 价格查询类问题先 sql+语义 检索,再传 LLM 引用
  - 切换 provider 只改 config.yaml,不动代码
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from packages.server.db.database import get_db
from packages.server.db.models import ChatSession, ChatMessage, Project
from packages.server.ai.chat_engine import answer

router = APIRouter()


class SessionOut(BaseModel):
    id: int
    project_id: Optional[int]
    title: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


class MessageIn(BaseModel):
    content: str
    use_rag: bool = True


class MessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    tool_calls: Optional[dict]
    created_at: datetime
    class Config:
        from_attributes = True


@router.post("/sessions", response_model=SessionOut)
def create_session(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    s = ChatSession(project_id=project_id, title=f"会话-{datetime.now().strftime('%m-%d %H:%M')}")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/sessions", response_model=List[SessionOut])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()


@router.get("/sessions/{sid}/messages", response_model=List[MessageOut])
def list_messages(sid: int, db: Session = Depends(get_db)):
    return db.query(ChatMessage).filter(ChatMessage.session_id == sid).order_by(ChatMessage.created_at).all()


@router.post("/sessions/{sid}/messages", response_model=MessageOut)
def send_message(sid: int, m: MessageIn, db: Session = Depends(get_db)):
    """发送消息: 经 RAG -> AI -> 入库 -> 返回"""
    session = db.query(ChatSession).get(sid)
    if not session:
        raise HTTPException(404, "会话不存在")

    user_msg = ChatMessage(session_id=sid, role="user", content=m.content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == sid)
        .order_by(ChatMessage.created_at)
        .all()
    )
    history_msgs = [{"role": h.role, "content": h.content} for h in history[:-1]]

    project_ctx = None
    if session.project_id:
        proj = db.query(Project).get(session.project_id)
        if proj:
            project_ctx = {"name": proj.name, "region": proj.region, "stage": proj.stage}

    result = answer(
        user_text=m.content,
        history=history_msgs,
        project_ctx=project_ctx,
        use_rag=m.use_rag,
    )

    # 把来源附在 content 末尾,前端显示
    content = result["content"]
    src = result["sources"]
    if (src["semantic"] or src["structured"]) and result["ok"]:
        refs = ["\n\n---\n引用来源:"]
        for i, r in enumerate(src["structured"][:3], 1):
            refs.append(f"[结构{i}] {r.get('item_name','')} | {r.get('specialty','')} | 单价: {r.get('price','')} | 来源: {r.get('source_file','')}")
        for i, r in enumerate(src["semantic"][:3], 1):
            refs.append(f"[语义{i}] 来源: {r.get('metadata',{}).get('source','?')} (相似度 {r.get('score',0):.2f})")
        content += "\n".join(refs)

    ai_msg = ChatMessage(session_id=sid, role="assistant", content=content)
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    return ai_msg
