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
import re
from typing import List, Dict, Optional, Any

from packages.server.ai.prompts import build_messages, SYSTEM_PROMPT
from packages.server.ai.client import get_ai_client, AIClientError, AIConfigError


def _extract_keywords(text: str) -> str:
    """从用户问题中提取价格查询关键词

    去掉"查一下/查询/帮我查/价格/单价/综合单价/是多少/多少钱/多少"等前缀后缀,
    如果没提取到,返回原文本。
    """
    # 常见查询前缀
    text = re.sub(
        r'^(查一下|查询|帮我查|帮我查一下|我想查|我要查|看看|搜一下|搜索)\s*',
        '', text
    )
    # 常见查询后缀
    text = re.sub(
        r'(的(综合单价|单价|价格|市场价|信息价|报价|多少钱|是多少)|'
        r'(综合单价|单价|价格|多少钱)是多少|'
        r'是多少钱|多少钱一个|价格多少|报价多少)\s*$',
        '', text
    )
    # 去掉标点
    text = re.sub(r'[，。！？、：；""''【】（）]', '', text)
    return text.strip() or ''



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
        # 提取关键词用于检索
        keywords = _extract_keywords(user_text)

        # 1. 语义检索
        try:
            from packages.server.ai.rag import search as rag_search
            semantic_hits = rag_search(keywords, top_k=top_k)
        except RuntimeError as e:
            # RAG 未就绪,降级为纯 LLM
            pass
        except Exception:
            pass

        # 2. 结构化查 SQL 价格库
        try:
            from packages.server.db.database import SessionLocal
            from packages.server.db.models import PriceUnit, Specialty
            db = SessionLocal()
            try:
                q = f"%{keywords}%"
                rows = (
                    db.query(PriceUnit, Specialty.name)
                    .join(Specialty, PriceUnit.specialty_id == Specialty.id)
                    .filter(PriceUnit.item_name.like(q))
                    .limit(top_k)
                    .all()
                )
                structured_hits = [
                    {
                        "item_name": r.item_name,
                        "specialty": spec_name,
                        "unit": r.unit, "price": r.price,
                        "region": r.region, "source_file": r.source_file,
                    }
                    for r, spec_name in rows
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
