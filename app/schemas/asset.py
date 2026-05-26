"""资产相关 Schema（固定资产实例、领用记录、报废单）"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# ── 固定资产实例 ──

class AssetInstanceCreate(BaseModel):
    """创建资产实例（通常由采购入库自动生成）"""
    item_id: int
    asset_code: str = Field(default="", max_length=50)
    serial_number: str = Field(default="", max_length=100)
    warehouse_id: int
    purchase_date: date
    notes: str = Field(default="")


class AssetInstanceUpdate(BaseModel):
    """更新资产实例"""
    asset_code: Optional[str] = Field(default=None, max_length=50)
    serial_number: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = None
    current_user_id: Optional[int] = None
    current_department_id: Optional[int] = None
    notes: Optional[str] = None


class AssetAssignRequest(BaseModel):
    """固定资产领用请求"""
    asset_instance_id: int
    assigned_to_user_id: int
    assigned_to_department_id: int
    assignment_date: date
    expected_return_date: Optional[date] = None
    notes: str = Field(default="")


class AssetReturnRequest(BaseModel):
    """固定资产交回请求"""
    return_date: date
    notes: str = Field(default="")


class AssetTransferRequest(BaseModel):
    """固定资产转移请求（换人/换部门）"""
    new_user_id: int
    new_department_id: int
    notes: str = Field(default="")


class AssetRepairRequest(BaseModel):
    """资产送修请求"""
    notes: str = Field(default="")


class AssetRepairDoneRequest(BaseModel):
    """资产修复完成请求"""
    notes: str = Field(default="")


# ── 报废单 ──

class DisposalCreate(BaseModel):
    """创建报废申请"""
    asset_instance_id: int
    disposal_type: str = Field(..., description="报废/出售/捐赠/丢失")
    reason: str = Field(default="")
    residual_value: float = Field(default=0.0, ge=0)
    notes: str = Field(default="")


class DisposalApproveRequest(BaseModel):
    """审核报废单"""
    comment: str = Field(default="")


class DisposalRejectRequest(BaseModel):
    """驳回报废单"""
    comment: str = Field(..., min_length=1)
