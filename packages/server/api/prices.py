"""价格库 API"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pydantic import BaseModel

from packages.server.db.database import get_db
from packages.server.db.models import (
    Specialty, PriceUnit, TopicPrice, RegionInfoPrice
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class PriceUnitOut(BaseModel):
    id: int
    specialty: Optional[str]
    item_name: str
    unit: str
    price: str
    region: str
    calc_rule: Optional[str]
    remark: Optional[str]
    source_file: Optional[str]

    class Config:
        from_attributes = True


class TopicPriceOut(BaseModel):
    id: int
    topic: str
    item_name: str
    unit: str
    price: str
    source_file: Optional[str]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.get("/specialties")
def list_specialties(db: Session = Depends(get_db)):
    """列出 8 大专业"""
    return [
        {"id": s.id, "name": s.name, "code": s.code, "description": s.description}
        for s in db.query(Specialty).all()
    ]


@router.get("/stats")
def prices_stats(db: Session = Depends(get_db)):
    """价格库统计"""
    specialty_stats = (
        db.query(Specialty.name, func.count(PriceUnit.id))
        .join(PriceUnit, PriceUnit.specialty_id == Specialty.id)
        .group_by(Specialty.name)
        .all()
    )
    topic_stats = (
        db.query(TopicPrice.topic, func.count(TopicPrice.id))
        .group_by(TopicPrice.topic)
        .all()
    )
    return {
        "total_prices": db.query(PriceUnit).count(),
        "by_specialty": {k: v for k, v in specialty_stats},
        "total_topics": db.query(TopicPrice).count(),
        "by_topic": {k: v for k, v in topic_stats},
        "total_region_info": db.query(RegionInfoPrice).count(),
    }


@router.get("", response_model=List[PriceUnitOut])
def list_prices(
    specialty: Optional[str] = None,
    region: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """列表查价(分页)"""
    q = db.query(PriceUnit, Specialty.name).join(Specialty, PriceUnit.specialty_id == Specialty.id)
    if specialty:
        q = q.filter(Specialty.name == specialty)
    if region:
        q = q.filter(PriceUnit.region == region)
    if keyword:
        q = q.filter(PriceUnit.item_name.like(f"%{keyword}%"))
    q = q.order_by(PriceUnit.id).offset(offset).limit(limit)
    results = []
    for pu, spec_name in q.all():
        results.append(PriceUnitOut(
            id=pu.id, specialty=spec_name, item_name=pu.item_name,
            unit=pu.unit, price=pu.price, region=pu.region,
            calc_rule=pu.calc_rule, remark=pu.remark, source_file=pu.source_file,
        ))
    return results


@router.get("/search", response_model=List[PriceUnitOut])
def search_prices(
    q: str = Query(..., min_length=1, description="项目名关键词"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    """模糊搜索价格(SQL LIKE)

    MVP 阶段用 LIKE;后续 M2 升级为 FTS5 全文索引
    """
    pattern = f"%{q}%"
    query = (
        db.query(PriceUnit, Specialty.name)
        .join(Specialty, PriceUnit.specialty_id == Specialty.id)
        .filter(or_(
            PriceUnit.item_name.like(pattern),
            PriceUnit.remark.like(pattern),
            PriceUnit.source_file.like(pattern),
        ))
        .order_by(PriceUnit.id)
        .limit(limit)
    )
    results = []
    for pu, spec_name in query.all():
        results.append(PriceUnitOut(
            id=pu.id, specialty=spec_name, item_name=pu.item_name,
            unit=pu.unit, price=pu.price, region=pu.region,
            calc_rule=pu.calc_rule, remark=pu.remark, source_file=pu.source_file,
        ))
    return results


@router.get("/topics", response_model=List[TopicPriceOut])
def list_topic_prices(
    topic: Optional[str] = None,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
):
    """市政重点专题"""
    q = db.query(TopicPrice)
    if topic:
        q = q.filter(TopicPrice.topic == topic)
    return q.order_by(TopicPrice.id).limit(limit).all()
