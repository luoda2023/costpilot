"""知识库 RAG API

提供:
  GET  /api/v1/kb/stats                索引统计(块数/已处理文件数)
  POST /api/v1/kb/search                语义检索
  POST /api/v1/kb/hybrid                混合检索(语义 + SQL 价格库)
  POST /api/v1/kb/reindex               触发增量重建(在线上跑)
  GET  /api/v1/kb/progress              查看索引进度
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from packages.server.ai.rag import search as rag_search, count as rag_count
from packages.server.db.database import SessionLocal
from packages.server.db.models import PriceUnit, Specialty

router = APIRouter()


class SearchIn(BaseModel):
    query: str
    top_k: Optional[int] = 5


@router.get("/stats")
def stats():
    """索引统计"""
    try:
        n = rag_count()
        return {"ok": True, "chunks": n, "embedding_model": "BAAI/bge-m3"}
    except RuntimeError as e:
        return {"ok": False, "msg": str(e), "chunks": 0}


@router.post("/search")
def search(s: SearchIn):
    """纯语义检索"""
    try:
        results = rag_search(s.query, top_k=s.top_k)
        return {"ok": True, "query": s.query, "count": len(results), "results": results}
    except RuntimeError as e:
        raise HTTPException(503, f"RAG 未就绪: {e}")
    except Exception as e:
        raise HTTPException(500, f"检索失败: {e}")


@router.post("/hybrid")
def hybrid_search(s: SearchIn):
    """混合检索: 语义 + SQL 价格库结构化查询

    策略:
      1. 从 query 用关键词识别 + 抽取专业/地区
      2. 跑 SQL LIKE 查 t_price_unit (结构化匹配)
      3. 同时跑语义检索 chunks (非结构化)
      4. 合并去重,标记来源
    """
    out = {"query": s.query, "structured": [], "semantic": []}

    # ---- 结构化查询(SQL 价格库)----
    db = SessionLocal()
    try:
        q = f"%{s.query}%"
        rows = db.query(PriceUnit).filter(PriceUnit.item_name.like(q)).limit(s.top_k or 5).all()
        out["structured"] = [
            {
                "item_name": r.item_name,
                "specialty": r.specialty.name if r.specialty else None,
                "unit": r.unit,
                "price": r.price,
                "region": r.region,
                "source_file": r.source_file,
            }
            for r in rows
        ]
    finally:
        db.close()

    # ---- 语义检索 ----
    try:
        out["semantic"] = rag_search(s.query, top_k=s.top_k)
        out["ok"] = True
    except RuntimeError as e:
        out["ok"] = False
        out["semantic_error"] = str(e)

    return out


@router.get("/progress")
def progress():
    """查索引处理进度"""
    from pathlib import Path
    import json
    PROGRESS_FILE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "chroma" / ".processed.json"
    if not PROGRESS_FILE.exists():
        return {"files": 0, "msg": "尚未开始扫描"}
    try:
        d = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        ok = sum(1 for v in d.values() if not v.get("error"))
        err = sum(1 for v in d.values() if v.get("error"))
        return {"files": len(d), "ok": ok, "error": err}
    except Exception as e:
        return {"files": 0, "msg": str(e)}
