"""FastAPI 依赖注入：数据库连接、认证、权限"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from app.database import get_connection
from app.utils.security import verify_token
from app.config import settings

security = HTTPBearer()


def get_db():
    """数据库连接依赖注入"""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn=Depends(get_db),
) -> dict:
    """从 JWT 令牌解析当前登录用户"""
    try:
        payload = verify_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    user = conn.execute(text(
        "SELECT id, username, display_name, role, email, phone, is_active FROM users WHERE id = :uid"
    ), {"uid": int(payload["sub"])}).fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="账号已被停用")

    return dict(user)


def require_role(*roles: str):
    """角色权限依赖工厂，返回一个检查当前用户角色的依赖函数"""

    def checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user

    return checker
