"""费率 API (规费/措施费/税金)"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from packages.server.db.database import get_db
from packages.server.db.models import FeeRate

router = APIRouter()


class FeeRateOut(BaseModel):
    id: int
    region: str
    fee_type: str
    fee_subitem: Optional[str]
    rate: float
    calc_base: Optional[str]
    remark: Optional[str]
    source_file: Optional[str]

    class Config:
        from_attributes = True


@router.get("", response_model=List[FeeRateOut])
def list_fees(
    region: Optional[str] = None,
    fee_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """查询各地规费/措施费/税金费率"""
    q = db.query(FeeRate)
    if region:
        q = q.filter(FeeRate.region == region)
    if fee_type:
        q = q.filter(FeeRate.fee_type == fee_type)
    return q.order_by(FeeRate.region, FeeRate.fee_type, FeeRate.fee_subitem).all()
