"""AI 智能导入匹配 API

提供:
POST /api/v1/quotes/ai-match  批量智能匹配 Excel 导入行到价格库

流程:
1. 对每行做 SQL LIKE 粗筛, 取 top 10 候选
2. 评分排序(完全匹配 100 → 包含 50 → 关键词 10)
3. 高分行(>30)直接返回
4. 低分行批量发给 AI 精匹配, 让 AI 理解语义做最佳匹配
"""
import json
import re
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from packages.server.db.database import get_db
from packages.server.db.models import PriceUnit, Specialty
from packages.server.ai.client import get_ai_client, AIClientError, AIConfigError

router = APIRouter()

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ImportRowIn(BaseModel):
    """Excel 导入的一行"""
    item_name: str
    qty: float = 0
    unit: str = ""
    specialty: str = ""
    price: float = 0


class AiMatchIn(BaseModel):
    """批量导入请求"""
    rows: List[ImportRowIn]


class MatchResultOut(BaseModel):
    """匹配结果"""
    item_name: str
    qty: float
    unit: str
    price: float
    specialty: str
    matched_price_id: Optional[int] = None
    matched_item_name: Optional[str] = None
    confidence: str = "none"  # high / medium / low / none
    remark: str = ""


class AiMatchOut(BaseModel):
    """批量匹配响应"""
    matched: List[MatchResultOut]
    stats: dict


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _clean_keyword(text: str) -> str:
    """从项目名中提取搜索关键词"""
    # 去标点
    text = re.sub(r'[，。！？、：；""''【】（）\s\-_/]', '', text)
    # 去常见项目名后缀
    text = re.sub(r'(项目|工程|清单|项)$', '', text)
    return text.strip()


def _score_item(name: str, candidate_name: str, unit: str = "", candidate_unit: str = "") -> int:
    """评分: 完全匹配 100 → 包含 50 → 关键词 10"""
    if not name or not candidate_name:
        return 0
    score = 0
    # 完全匹配
    if name == candidate_name:
        score = 100
    elif candidate_name in name or name in candidate_name:
        score = 50
    else:
        # 关键词匹配
        keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', name)
        for kw in keywords:
            if len(kw) >= 2 and kw in candidate_name:
                score += 10
    # 单位一致加分
    if unit and candidate_unit and unit == candidate_unit:
        score += 5
    return score


def _generate_ai_prompt(rows_info: list) -> str:
    """为 AI 生成匹配提示词"""
    prompt_parts = [
        "你是一个造价工程师,帮助将清单项目匹配到价格库中的综合单价。",
        "对于每个清单项目,从价格库候选列表中选择最匹配的综合单价。",
        "如果找到匹配,返回格式: 序号|价格库项目名|价格库ID|单位|综合单价|专业",
        "如果无法匹配,返回格式: 序号|无匹配|||",
        "注意: 单位可以换算(如 m³ 和 m² 不能互换,但 t 和 kg 可以换算)",
        "",
        "清单项目:",
    ]
    for item in rows_info:
        candidates_str = "; ".join(
            [f"{c['name']}({c['unit']}/{c['price']}/{c['specialty']})" for c in item['candidates'][:5]]
        )
        prompt_parts.append(
            f"序号{item['idx']}: 项目名={item['name']}, 单位={item['unit']}, "
            f"候选=[{candidates_str}]"
        )
    prompt_parts.append("")
    prompt_parts.append("请按格式输出匹配结果,每行一个:")
    return "\n".join(prompt_parts)


def _parse_ai_response(response_text: str, rows_info: list) -> dict:
    """解析 AI 返回的匹配结果"""
    matches = {}
    for line in response_text.strip().split('\n'):
        line = line.strip()
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 2 and parts[0].isdigit():
                idx = int(parts[0])
                if parts[1] and parts[1] != '无匹配':
                    try:
                        matches[idx] = {
                            'matched_item_name': parts[1],
                            'matched_price_id': int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None,
                            'unit': parts[3] if len(parts) > 3 else '',
                            'price': float(parts[4].replace('元','').replace(',','')) if len(parts) > 4 and parts[4] else 0,
                            'specialty': parts[5] if len(parts) > 5 else '',
                        }
                    except (ValueError, IndexError):
                        pass
    return matches


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.post("/ai-match", response_model=AiMatchOut)
def ai_match_import(
    payload: AiMatchIn,
    db: Session = Depends(get_db),
):
    """AI 智能导入匹配: 对 Excel 导入行批量匹配价格库"""
    if not payload.rows:
        return AiMatchOut(matched=[], stats={"total": 0, "matched": 0, "unmatched": 0, "ai_matched": 0})

    results = []
    fuzzy_rows = []  # 需要 AI 精匹配的行
    fuzzy_indices = {}  # idx -> index in fuzzy_rows

    for idx, row in enumerate(payload.rows):
        name = row.item_name.strip()
        if not name:
            results.append(MatchResultOut(
                item_name=row.item_name, qty=row.qty, unit=row.unit,
                price=row.price, specialty=row.specialty, confidence="none",
                remark="项目名称为空"
            ))
            continue

        # Step 1: 关键词提取
        keyword = _clean_keyword(name)
        if not keyword:
            keyword = name[:6]

        # Step 2: SQL 粗筛, 取 top 10
        pattern = f"%{keyword}%"
        candidates = (
            db.query(PriceUnit, Specialty.name)
            .join(Specialty, PriceUnit.specialty_id == Specialty.id)
            .filter(PriceUnit.item_name.like(pattern))
            .order_by(PriceUnit.id)
            .limit(10)
            .all()
        )

        if not candidates:
            # 无候选, 留待 AI 处理
            fuzzy_rows.append({
                'idx': idx,
                'name': name,
                'unit': row.unit,
                'candidates': [],
            })
            fuzzy_indices[idx] = len(fuzzy_rows) - 1
            continue

        # Step 3: 评分排序
        scored = []
        for pu, spec_name in candidates:
            score = _score_item(name, pu.item_name, row.unit, pu.unit)
            scored.append((score, pu, spec_name))
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score, best_pu, best_spec = scored[0]

        if best_score >= 30:
            # 高分匹配, 直接返回
            price_val = 0
            try:
                price_str = best_pu.price.split(' ')[0] if best_pu.price else '0'
                price_val = float(price_str.replace(',', '').replace('元', ''))
            except ValueError:
                price_val = 0

            results.append(MatchResultOut(
                item_name=row.item_name,
                qty=row.qty,
                unit=best_pu.unit,
                price=price_val,
                specialty=best_spec,
                matched_price_id=best_pu.id,
                matched_item_name=best_pu.item_name,
                confidence="high" if best_score >= 80 else "medium",
                remark=f"匹配: {best_pu.item_name} ({best_pu.unit})"
            ))
        else:
            # 低分, 留待 AI 精匹配
            candidate_list = [
                {'name': pu.item_name, 'unit': pu.unit, 'price': pu.price, 'specialty': spec_name, 'id': pu.id}
                for score, pu, spec_name in scored[:5]
            ]
            fuzzy_rows.append({
                'idx': idx,
                'name': name,
                'unit': row.unit,
                'candidates': candidate_list,
            })
            fuzzy_indices[idx] = len(fuzzy_rows) - 1

    # Step 4: AI 批量精匹配
    ai_matched = {}
    if fuzzy_rows:
        try:
            client = get_ai_client()
            prompt = _generate_ai_prompt(fuzzy_rows)
            resp = client.chat(messages=[
                {"role": "system", "content": "你是一个造价工程师,负责匹配清单项目到价格库综合单价。请严格按照格式输出。"},
                {"role": "user", "content": prompt},
            ])
            ai_text = resp.get("content", "")
            ai_matched = _parse_ai_response(ai_text, fuzzy_rows)
        except (AIClientError, AIConfigError):
            pass  # AI 不可用, 保留未匹配状态

    # 填充 AI 匹配结果
    for frow in fuzzy_rows:
        idx = frow['idx']
        name = frow['name']
        unit = frow['unit']
        match = ai_matched.get(idx)

        if match and match.get('matched_price_id'):
            results.append(MatchResultOut(
                item_name=name,
                qty=payload.rows[idx].qty,
                unit=match.get('unit', unit),
                price=match.get('price', 0),
                specialty=match.get('specialty', ''),
                matched_price_id=match['matched_price_id'],
                matched_item_name=match.get('matched_item_name', ''),
                confidence="low",
                remark=f"AI匹配: {match.get('matched_item_name', '')}"
            ))
        else:
            # 无匹配, 保留原始数据
            results.append(MatchResultOut(
                item_name=name,
                qty=payload.rows[idx].qty,
                unit=unit,
                price=payload.rows[idx].price,
                specialty=payload.rows[idx].specialty,
                confidence="none",
                remark="未匹配到价格库"
            ))

    # 统计
    matched_count = sum(1 for r in results if r.confidence in ("high", "medium"))
    ai_matched_count = sum(1 for r in results if r.confidence == "low")
    unmatched_count = sum(1 for r in results if r.confidence == "none")

    return AiMatchOut(
        matched=results,
        stats={
            "total": len(results),
            "matched": matched_count + ai_matched_count,
            "ai_matched": ai_matched_count,
            "unmatched": unmatched_count,
        }
    )