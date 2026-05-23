"""用户管理路由（管理员专用）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from app.api.deps import get_db, get_current_user, require_role
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password

router = APIRouter(prefix="/api/v1/users", tags=["用户管理"])


@router.get("/")
def list_users(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    admin: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """用户列表（分页）"""
    where = "WHERE 1=1"
    params = {}
    if keyword:
        where += " AND (username LIKE :kw1 OR display_name LIKE :kw2)"
        params["kw1"] = f"%{keyword}%"
        params["kw2"] = f"%{keyword}%"

    total = conn.execute(text(f"SELECT COUNT(*) FROM users {where}"), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset
    rows = conn.execute(text(
        f"SELECT id, username, display_name, role, email, phone, is_active, created_at FROM users {where} ORDER BY id DESC LIMIT :limit OFFSET :offset"
    ), params).fetchall()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/")
def create_user(
    body: UserCreate,
    admin: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """创建用户"""
    existing = conn.execute(text("SELECT id FROM users WHERE username = :un"), {"un": body.username}).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    conn.execute(text(
        "INSERT INTO users (username, password_hash, display_name, role, email, phone) VALUES (:un, :ph, :dn, :r, :em, :p)"
    ), {"un": body.username, "ph": hash_password(body.password), "dn": body.display_name, "r": body.role, "em": body.email, "p": body.phone})
    conn.commit()
    return {"message": "用户创建成功"}


@router.get("/{user_id}")
def get_user(
    user_id: int,
    admin: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """获取用户详情"""
    user = conn.execute(text(
        "SELECT id, username, display_name, role, email, phone, is_active, created_at FROM users WHERE id = :uid"
    ), {"uid": user_id}).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return dict(user)


@router.put("/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    admin: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """更新用户信息"""
    user = conn.execute(text("SELECT id FROM users WHERE id = :uid"), {"uid": user_id}).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    updates = {}
    if body.display_name is not None:
        updates["display_name"] = body.display_name
    if body.email is not None:
        updates["email"] = body.email
    if body.phone is not None:
        updates["phone"] = body.phone
    if body.role is not None:
        updates["role"] = body.role

    if updates:
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        params = {k: v for k, v in updates.items()}
        params["uid"] = user_id
        conn.execute(text(f"UPDATE users SET {set_clause}, updated_at = NOW() WHERE id = :uid"), params)
        conn.commit()

    return {"message": "用户信息更新成功"}


@router.put("/{user_id}/toggle")
def toggle_user(
    user_id: int,
    admin: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """启用/停用用户"""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="不能停用自己")

    user = conn.execute(text("SELECT id, is_active FROM users WHERE id = :uid"), {"uid": user_id}).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_status = 0 if user["is_active"] else 1
    conn.execute(text(
        "UPDATE users SET is_active = :st, updated_at = NOW() WHERE id = :uid"
    ), {"st": new_status, "uid": user_id})
    conn.commit()
    return {"message": f"用户已{'启用' if new_status else '停用'}"}


@router.put("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    admin: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """重置用户密码为默认密码"""
    user = conn.execute(text("SELECT id FROM users WHERE id = :uid"), {"uid": user_id}).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    conn.execute(text(
        "UPDATE users SET password_hash = :ph, updated_at = NOW() WHERE id = :uid"
    ), {"ph": hash_password("123456"), "uid": user_id})
    conn.commit()
    return {"message": "密码已重置为 123456"}
