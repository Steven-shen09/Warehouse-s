"""消耗品领用 Schema"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class ConsumableRecordCreate(BaseModel):
    """提交消耗品领用申请"""
    item_id: int
    quantity: int = Field(ge=1)
    pickup_date: date
    reason: str = Field(default="")
    source_warehouse_id: int


class ConsumableBatchRequest(BaseModel):
    """批量领用消耗品"""
    items: list["ConsumableBatchItem"]
    pickup_date: date
    reason: str = Field(default="")


class ConsumableBatchItem(BaseModel):
    """批量领用明细"""
    item_id: int
    quantity: int = Field(ge=1)
    source_warehouse_id: int


class ConsumableApproveRequest(BaseModel):
    """审核通过消耗品领用"""
    comment: str = Field(default="")


class ConsumableRejectRequest(BaseModel):
    """驳回消耗品领用"""
    comment: str = Field(..., min_length=1)
