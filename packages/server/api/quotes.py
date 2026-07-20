"""报价生成与导出 API

提供:
  POST /api/v1/quotes/compose              组价并返回 QuoteResult 结构
  POST /api/v1/quotes/export/excel          组价并导出 Excel
  POST /api/v1/quotes/export/word           组价并导出 Word
  GET  /api/v1/quotes/download/{filename}   下载已生成的文件
"""
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from packages.server.templates.pricing import QuantityItem, compose_quote, QuoteResult
from packages.server.templates.excel_export import export_quote_to_excel
from packages.server.templates.word_export import export_quote_to_word

router = APIRouter()

# 输出目录
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "exports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class QuantityIn(BaseModel):
    item_name: str
    unit: str
    qty: float
    price: float
    specialty: Optional[str] = None
    remark: Optional[str] = None


class ComposeIn(BaseModel):
    items: List[QuantityIn]
    region: str = "全国"
    stage: str = "预算"
    tax_method: str = "一般计税"   # 一般计税 / 简易计税


class ProjectInfoIn(BaseModel):
    name: str = "未命名项目"
    region: str = "全国"
    stage: str = "预算"
    tax_method: str = "一般计税"
    compiler: Optional[str] = None
    reviewer: Optional[str] = None
    date: Optional[str] = None


class ExportIn(BaseModel):
    items: List[QuantityIn]
    project_info: ProjectInfoIn


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.post("/compose")
def compose(payload: ComposeIn):
    """组价并返回完整结果(不导出文件)"""
    items = [QuantityItem(**q.model_dump()) for q in payload.items]
    quote = compose_quote(
        items,
        region=payload.region,
        stage=payload.stage,
        tax_method=payload.tax_method,
    )
    return {
        "stage": quote.stage,
        "region": quote.region,
        "tax_method": quote.tax_method,
        "category1": quote.category1,
        "category2": quote.category2,
        "category3": quote.category3,
        "category2_detail": quote.category2_detail,
        "category3_detail": quote.category3_detail,
        "grand_total": quote.grand_total,
        "items": [
            {
                "item_name": c.item.item_name,
                "unit": c.item.unit,
                "qty": c.item.qty,
                "price": c.item.price,
                "specialty": c.item.specialty,
                "remark": c.item.remark,
                "total": c.total,
            }
            for c in quote.items
        ],
    }


@router.post("/export/excel")
def export_excel(payload: ExportIn):
    """组价并导出 Excel 文件,返回下载 URL"""
    items = [QuantityItem(**q.model_dump()) for q in payload.items]
    quote = compose_quote(
        items,
        region=payload.project_info.region,
        stage=payload.project_info.stage,
        tax_method=payload.project_info.tax_method,
    )
    project_info = payload.project_info.model_dump()
    if not project_info.get("date"):
        project_info["date"] = datetime.now().strftime("%Y-%m-%d")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{project_info['name']}_报价表_{timestamp}.xlsx"
    output_path = OUTPUT_DIR / filename
    actual = export_quote_to_excel(quote, project_info, str(output_path))

    return {
        "ok": True,
        "filename": filename,
        "path": actual,
        "size_kb": round(os.path.getsize(actual) / 1024, 1),
        "download_url": f"/api/v1/quotes/download/{filename}",
        "grand_total": quote.grand_total,
    }


@router.post("/export/word")
def export_word(payload: ExportIn):
    """组价并导出 Word 文件"""
    items = [QuantityItem(**q.model_dump()) for q in payload.items]
    quote = compose_quote(
        items,
        region=payload.project_info.region,
        stage=payload.project_info.stage,
        tax_method=payload.project_info.tax_method,
    )
    project_info = payload.project_info.model_dump()
    if not project_info.get("date"):
        project_info["date"] = datetime.now().strftime("%Y-%m-%d")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{project_info['name']}_报价表_{timestamp}.docx"
    output_path = OUTPUT_DIR / filename
    actual = export_quote_to_word(quote, project_info, str(output_path))

    return {
        "ok": True,
        "filename": filename,
        "path": actual,
        "size_kb": round(os.path.getsize(actual) / 1024, 1),
        "download_url": f"/api/v1/quotes/download/{filename}",
        "grand_total": quote.grand_total,
    }


@router.get("/download/{filename}")
def download_file(filename: str):
    """下载已生成的报价文件"""
    # 防 path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "非法文件名")
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "文件不存在或已清理")
    return FileResponse(str(path), filename=filename)
