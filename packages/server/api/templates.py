"""模板 API"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from packages.server.db.database import get_db
from packages.server.db.models import (
    TemplateType, Template, TemplateField
)

router = APIRouter()


class TemplateTypeOut(BaseModel):
    id: int
    name: str
    doc_type: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class TemplateOut(BaseModel):
    id: int
    type_id: int
    name: str
    content_md: str
    yaml_skeleton: Optional[str]
    version: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/types", response_model=List[TemplateTypeOut])
def list_types(db: Session = Depends(get_db)):
    """列出 8 类格式谱"""
    return db.query(TemplateType).all()


@router.get("", response_model=List[TemplateOut])
def list_templates(type_id: Optional[int] = None, db: Session = Depends(get_db)):
    """列出模板列表"""
    q = db.query(Template).filter(Template.is_active == True)
    if type_id:
        q = q.filter(Template.type_id == type_id)
    return q.all()


@router.get("/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """获取单个模板"""
    t = db.query(Template).get(template_id)
    if not t:
        raise HTTPException(404, "模板不存在")
    return t


@router.get("/{template_id}/fields")
def get_template_fields(template_id: int, db: Session = Depends(get_db)):
    """获取模板字段定义"""
    fields = db.query(TemplateField).filter(TemplateField.template_id == template_id).all()
    return [
        {
            "id": f.id, "field_key": f.field_key, "field_label": f.field_label,
            "field_type": f.field_type, "required": f.required,
            "default_value": f.default_value, "options": f.options,
        }
        for f in fields
    ]


# ---------------------------------------------------------------------------
# M2.5: 文档生成
# ---------------------------------------------------------------------------

from fastapi import UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel as PydBaseModel
import os
from pathlib import Path
from datetime import datetime

from packages.server.templates.doc_renderer import export_template_to_docx


class RenderIn(PydBaseModel):
    template_id: int
    field_values: dict


@router.post("/render")
def render_template(payload: RenderIn):
    """根据模板 ID + 字段值,生成 docx,返回下载 URL"""
    try:
        out_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = out_dir / f"template_{payload.template_id}_{timestamp}.docx"
        actual = export_template_to_docx(payload.template_id, payload.field_values, str(output))
        return {
            "ok": True,
            "filename": Path(actual).name,
            "path": actual,
            "size_kb": round(os.path.getsize(actual)/1024, 1),
            "download_url": f"/api/v1/templates/download/{Path(actual).name}",
        }
    except Exception as e:
        raise HTTPException(500, f"渲染失败: {e}")


@router.get("/download/{filename}")
def download_template_file(filename: str):
    """下载已渲染的模板 docx"""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "非法文件名")
    out_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "exports"
    path = out_dir / filename
    if not path.exists():
        raise HTTPException(404, "文件不存在")
    return FileResponse(str(path), filename=filename)
