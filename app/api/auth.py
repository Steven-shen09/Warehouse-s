"""认证路由：登录、登出、获取当前用户、修改密码"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.api.deps import get_db, get_current_user
from app.schemas.auth import LoginRequest, ChangePasswordRequest
from app.utils.security import verify_password, hash_password, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/login")
def login(body: LoginRequest, conn=Depends(get_db)):
    """用户登录，返回 JWT 并设置 Cookie"""
    user = conn.execute(text(
        "SELECT id, username, password_hash, display_name, role, email, phone, is_active FROM users WHERE username = :un"
    ), {"un": body.username}).fetchone()

    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="账号已被停用")

    token = create_access_token(user["id"], user["username"], user["role"])
    user_data = {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
        "email": user["email"],
        "phone": user["phone"],
    }
    resp = JSONResponse(content={"access_token": token, "token_type": "bearer", "user": user_data})
    resp.set_cookie(
        key="warehouse_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax",
    )
    return resp


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {"user": current_user}


@router.put("/change-password")
def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """修改密码"""
    user = conn.execute(text(
        "SELECT password_hash FROM users WHERE id = :uid"
    ), {"uid": current_user["id"]}).fetchone()

    if not verify_password(body.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="原密码错误")

    new_hash = hash_password(body.new_password)
    conn.execute(text(
        "UPDATE users SET password_hash = :ph, updated_at = NOW() WHERE id = :uid"
    ), {"ph": new_hash, "uid": current_user["id"]})
    conn.commit()
    return {"message": "密码修改成功"}
