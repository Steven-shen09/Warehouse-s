"""用户管理 Schema"""
from pydantic import BaseModel, Field
from typing import Optional


class UserCreate(BaseModel):
    """创建用户"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6)
    display_name: str = Field(default="")
    role: str = Field(default="user", pattern="^(admin|approver|user)$")
    email: str = Field(default="")
    phone: str = Field(default="")


class UserUpdate(BaseModel):
    """更新用户信息"""
    display_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = Field(default=None, pattern="^(admin|approver|user)$")


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    display_name: str
    role: str
    email: str
    phone: str
    is_active: int
    created_at: str
