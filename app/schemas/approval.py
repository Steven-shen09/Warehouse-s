"""审核 Schema"""
from pydantic import BaseModel, Field


class ApproveRequest(BaseModel):
    """审核通过"""
    comment: str = Field(default="", description="审核意见")


class RejectRequest(BaseModel):
    """审核驳回"""
    comment: str = Field(..., min_length=1, description="驳回原因（必填）")
