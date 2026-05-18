"""物品管理 Schema"""
from pydantic import BaseModel, Field
from typing import Optional


class ItemCreate(BaseModel):
    """创建物品"""
    name: str = Field(..., min_length=1, max_length=100, description="物品名称")
    category: str = Field(default="", description="分类")
    description: str = Field(default="", description="描述")
    location: str = Field(default="", description="存放位置")
    total_quantity: int = Field(default=1, ge=1, description="总库存数量")
    value: float = Field(default=0.0, ge=0, description="物品单价")
    low_stock_threshold: int = Field(default=2, ge=0, description="低库存预警阈值")
    image_url: str = Field(default="", description="物品图片URL")


class ItemUpdate(BaseModel):
    """更新物品"""
    name: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    total_quantity: Optional[int] = Field(default=None, ge=1)
    value: Optional[float] = Field(default=None, ge=0)
    low_stock_threshold: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[str] = None


# ── 批量导入 Schema ──

class ImportPreviewRow(BaseModel):
    """导入预览单行"""
    index: int
    data: dict
    status: str  # "ok" | "duplicate" | "error"
    message: Optional[str] = None
    duplicate_item: Optional[dict] = None


class ImportConfirmRow(BaseModel):
    """确认导入单行选择"""
    index: int
    action: str  # "create" | "add_to_existing"
    item_id: Optional[int] = None  # 仅 add_to_existing 时需要


class ImportConfirmRequest(BaseModel):
    """确认导入请求"""
    rows: list[ImportConfirmRow]


class ImportResult(BaseModel):
    """导入结果"""
    message: str
    imported: int
    updated: int
    skipped: int
