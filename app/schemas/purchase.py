"""采购入库 Schema"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class PurchaseOrderCreate(BaseModel):
    """创建采购入库单"""
    supplier_id: int
    warehouse_id: int
    purchase_date: date
    notes: str = Field(default="")
    items: list["PurchaseOrderItemCreate"]


class PurchaseOrderItemCreate(BaseModel):
    """采购入库明细"""
    item_id: int
    quantity: int = Field(ge=1)
    unit_price: float = Field(default=0.0, ge=0)
    batch_no: str = Field(default="")
    production_date: Optional[date] = None
    expiry_date: Optional[date] = None
    notes: str = Field(default="")


class PurchaseOrderUpdate(BaseModel):
    """更新采购单"""
    supplier_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    purchase_date: Optional[date] = None
    notes: Optional[str] = None
