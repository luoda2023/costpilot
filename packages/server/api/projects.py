"""项目 API"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from packages.server.db.database import get_db
from packages.server.db.models import Project, Quantity, Quote

router = APIRouter()


class ProjectIn(BaseModel):
    name: str
    region: str
    stage: str  # 估算/概算/预算/结算
    note: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    region: str
    stage: str
    owner_id: Optional[int]
    status: str
    note: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuantityIn(BaseModel):
    specialty_id: Optional[int]
    item_name: str
    unit: str
    qty: float
    matched_price_id: Optional[int] = None
    custom_price: Optional[float] = None
    remark: Optional[str] = None


class QuantityOut(BaseModel):
    id: int
    project_id: int
    specialty_id: Optional[int]
    item_name: str
    unit: str
    qty: float
    matched_price_id: Optional[int]
    custom_price: Optional[float]
    remark: Optional[str]

    class Config:
        from_attributes = True


@router.get("", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    """列出所有项目"""
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectOut)
def create_project(p: ProjectIn, db: Session = Depends(get_db)):
    proj = Project(name=p.name, region=p.region, stage=p.stage, note=p.note)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


@router.get("/{pid}", response_model=ProjectOut)
def get_project(pid: int, db: Session = Depends(get_db)):
    proj = db.query(Project).get(pid)
    if not proj:
        raise HTTPException(404, "项目不存在")
    return proj


@router.delete("/{pid}")
def delete_project(pid: int, db: Session = Depends(get_db)):
    proj = db.query(Project).get(pid)
    if not proj:
        raise HTTPException(404, "项目不存在")
    db.delete(proj)
    db.commit()
    return {"ok": True}


@router.get("/{pid}/quantities", response_model=List[QuantityOut])
def list_quantities(pid: int, db: Session = Depends(get_db)):
    return db.query(Quantity).filter(Quantity.project_id == pid).all()


@router.post("/{pid}/quantities", response_model=QuantityOut)
def add_quantity(pid: int, q: QuantityIn, db: Session = Depends(get_db)):
    proj = db.query(Project).get(pid)
    if not proj:
        raise HTTPException(404, "项目不存在")
    qty = Quantity(project_id=pid, **q.model_dump())
    db.add(qty)
    db.commit()
    db.refresh(qty)
    return qty
