"""仓库管理、调拨、盘点 Schema"""
from pydantic import BaseModel, Field
from typing import Optional


# ── 仓库 ──

class WarehouseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="仓库名称")
    location: str = Field(default="", description="仓库地址")
    description: str = Field(default="", description="描述")


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=50)
    location: Optional[str] = None
    description: Optional[str] = None


# ── 调拨 ──

class TransferCreate(BaseModel):
    item_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    quantity: int = Field(..., ge=1, description="调拨数量")
    reason: str = Field(default="", description="调拨原因")


# ── 盘点 ──

class InventoryCountCreate(BaseModel):
    warehouse_id: int
    name: str = Field(..., min_length=1, max_length=100, description="盘点名称")


class InventoryCountItemUpdate(BaseModel):
    actual_quantity: Optional[int] = Field(default=None, description="实盘数量")
    notes: str = Field(default="", description="备注")
