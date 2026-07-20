"""
造价通 - 聊天编排引擎

把用户问题转化为 RAG + AI 的端到端回答:
  1. 接收用户问题
  2. RAG 检索相关知识 chunks + 价格库结构化查询
  3. 把检索结果作为 context 注入 system prompt
  4. 调外部 AI(OpenAI 兼容)生成回答
  5. 返回 {content, sources}

不绑模型: AI 由 config.yaml 选择(DeepSeek/Qwen/智谱/...)
"""
import json
from typing import List, Dict, Optional, Any

from packages.server.ai.prompts import build_messages, SYSTEM_PROMPT
from packages.server.ai.client import get_ai_client, AIClientError, AIConfigError


def _format_context(semantic_hits: List[Dict], structured_hits: List[Dict]) -> str:
    """把检索结果转为 system 注入的 context 字符串"""
    parts = []

    if structured_hits:
        parts.append("## 价格库匹配(结构化查询 t_price_unit)\n")
        for i, r in enumerate(structured_hits, 1):
            parts.append(
                f"{i}. {r.get('item_name','')} | {r.get('specialty','')} | "
                f"{r.get('unit','')} | 单价: {r.get('price','')} | "
                f"地区: {r.get('region','')} | 来源: {r.get('source_file','')}"
            )
        parts.append("")

    if semantic_hits:
        parts.append("## 知识库语义检索片段(chunks)\n")
        for i, r in enumerate(semantic_hits, 1):
            meta = r.get("metadata", {})
            parts.append(f"[片段{i} score={r.get('score',0):.2f} 来源={meta.get('source','?')}]")
            parts.append(r.get("text", "")[:500])
            parts.append("")

    return "\n".join(parts) if parts else "(无相关检索结果)"


def answer(
    user_text: str,
    history: Optional[List[Dict]] = None,
    project_ctx: Optional[Dict] = None,
    use_rag: bool = True,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    返回:
      {
        "content":  str,             # AI 回复
        "sources":  List[Dict],      # 引用来源(语义+结构化)
        "ok":       bool,
        "error":    str | None,
      }
    """
    semantic_hits = []
    structured_hits = []

    if use_rag:
        # 1. 语义检索
        try:
            from packages.server.ai.rag import search as rag_search
            semantic_hits = rag_search(user_text, top_k=top_k)
        except RuntimeError as e:
            # RAG 未就绪,降级为纯 LLM
            pass
        except Exception:
            pass

        # 2. 结构化查 SQL 价格库
        try:
            from packages.server.db.database import SessionLocal
            from packages.server.db.models import PriceUnit
            db = SessionLocal()
            try:
                q = f"%{user_text}%"
                rows = db.query(PriceUnit).filter(PriceUnit.item_name.like(q)).limit(top_k).all()
                structured_hits = [
                    {
                        "item_name": r.item_name,
                        "specialty": r.specialty.name if r.specialty else None,
                        "unit": r.unit, "price": r.price,
                        "region": r.region, "source_file": r.source_file,
                    }
                    for r in rows
                ]
            finally:
                db.close()
        except Exception:
            pass

    # 3. 注入 context 后的 messages
    msgs = build_messages(user_text, history, project_ctx)

    if use_rag and (semantic_hits or structured_hits):
        ctx = _format_context(semantic_hits, structured_hits)
        # 在 system 之后插一个 RAG context
        rag_msg = {"role": "system", "content": f"以下是知识库检索结果,引用时务必给出来源文件:\n\n{ctx}"}
        # 插在 system 之后,history 之前
        msgs.insert(1, rag_msg)

    # 4. 调 AI
    try:
        client = get_ai_client()
        resp = client.chat(msgs)
        return {
            "content": resp["content"] or "",
            "sources": {"semantic": semantic_hits, "structured": structured_hits},
            "ok": True, "error": None,
        }
    except (AIConfigError, AIClientError) as e:
        return {
            "content": f"[AI 调用失败] {e}",
            "sources": {"semantic": semantic_hits, "structured": structured_hits},
            "ok": False, "error": str(e),
        }
    except Exception as e:
        return {
            "content": f"[AI 异常] {e}",
            "sources": {"semantic": semantic_hits, "structured": structured_hits},
            "ok": False, "error": str(e),
        }


if __name__ == "__main__":
    print("Chat 引擎自测...")
    r = answer("北京某高层住宅 1# 楼,查一下 钢质防火门 的综合单价")
    print("OK:", r["ok"])
    print("Error:", r["error"])
    print("Sources:", len(r["sources"]["semantic"]), "语义 /", len(r["sources"]["structured"]), "结构化")
    print("Content:", r["content"][:200])
