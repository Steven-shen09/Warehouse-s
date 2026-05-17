"""租借记录 Schema"""
from pydantic import BaseModel, Field
from typing import Optional


class BorrowRequest(BaseModel):
    """租借申请"""
    item_id: int = Field(..., description="物品ID")
    quantity: int = Field(..., ge=1, description="租借数量")
    borrow_date: str = Field(..., description="借出日期 (YYYY-MM-DD)")
    expected_return_date: str = Field(..., description="预计归还日期 (YYYY-MM-DD)")
    reason: str = Field(default="", description="租借事由")
    contact: str = Field(default="", description="联系方式")


class BatchBorrowItem(BaseModel):
    """批量租借中的单个物品"""
    item_id: int = Field(..., description="物品ID")
    quantity: int = Field(..., ge=1, description="租借数量")


class BatchBorrowRequest(BaseModel):
    """批量租借申请（购物车模式）"""
    items: list[BatchBorrowItem] = Field(..., min_length=1, description="租借物品列表")
    borrow_date: str = Field(..., description="借出日期 (YYYY-MM-DD)")
    expected_return_date: str = Field(..., description="预计归还日期 (YYYY-MM-DD)")
    reason: str = Field(default="", description="租借事由")
    contact: str = Field(default="", description="联系方式")


class ReturnRequest(BaseModel):
    """归还请求"""
    return_quantity: int = Field(..., ge=1, description="归还数量")
    actual_return_date: str = Field(default="", description="实际归还日期")
    return_notes: str = Field(default="", description="归还备注")


class DocumentReturnRequest(BaseModel):
    """按单据归还请求"""
    actual_return_date: str = Field(default="", description="实际归还日期")
    return_notes: str = Field(default="", description="归还备注")
