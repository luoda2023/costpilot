"""文件浏览与预览 API (供前端预览模块)

提供:
- GET /api/v1/files/list?path=...        列出某目录
- GET /api/v1/preview/text?path=...      读取 txt/md 文本
- GET /api/v1/preview/file?path=...      原文件流(PDF/图片)
"""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse

# 文件浏览 router
router = APIRouter()

# 预览 router(独立挂在 /api/v1/preview 下)
preview_router = APIRouter()

# 限制可访问的根路径(防止越权访问)
ALLOWED_ROOTS = [
    "H:/AI-model",
    "H:\\AI-model",
]


def _safe_path(p: str) -> Path:
    """路径安全检查 - 必须在允许的根路径下"""
    if not p:
        raise HTTPException(400, "path 必填")
    full = Path(p).resolve()
    norm = str(full)
    if not any(norm.startswith(os.path.normpath(r)) or norm.startswith(r.replace("/", "\\")) for r in ALLOWED_ROOTS):
        raise HTTPException(403, f"无权访问此路径: {p}")
    return full


@router.get("/list")
def list_dir(path: str = Query(..., description="要列的目录绝对路径")):
    """列出某目录的子项"""
    full = _safe_path(path)
    if not full.exists() or not full.is_dir():
        raise HTTPException(404, f"目录不存在: {path}")

    items = []
    try:
        for child in sorted(full.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if child.name.startswith('.') or child.name.startswith('~'):
                continue
            try:
                stat = child.stat()
                items.append({
                    "name": child.name,
                    "path": str(child),
                    "is_dir": child.is_dir(),
                    "size": stat.st_size if child.is_file() else 0,
                })
            except (PermissionError, OSError):
                continue
    except PermissionError:
        raise HTTPException(403, f"无权读取: {path}")

    return {"path": str(full), "items": items}


@preview_router.get("/text")
def preview_text(path: str = Query(...)):
    """读取文本文件 (md/txt/markdown/yml/json/csv)"""
    full = _safe_path(path)
    if not full.exists() or not full.is_file():
        raise HTTPException(404, "文件不存在")
    ext = full.suffix.lower().lstrip(".")
    if ext not in {"md", "txt", "markdown", "yml", "yaml", "json", "csv", "log"}:
        raise HTTPException(400, f"不支持预览的文件类型: {ext}")
    try:
        text = full.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(500, f"读取失败: {e}")
    return PlainTextResponse(text, media_type="text/plain; charset=utf-8")


@preview_router.get("/file")
def preview_file(path: str = Query(...)):
    """返回原始文件流,供前端 iframe/img 预览 PDF/图片"""
    full = _safe_path(path)
    if not full.exists() or not full.is_file():
        raise HTTPException(404, "文件不存在")
    ext = full.suffix.lower().lstrip(".")
    allowed = {"pdf", "jpg", "jpeg", "png", "gif", "webp", "bmp"}
    if ext not in allowed:
        raise HTTPException(400, f"不支持内联预览的格式: {ext},请用系统默认程序打开")
    return FileResponse(str(full), filename=full.name)
