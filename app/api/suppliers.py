"""供应商管理路由"""
from sqlalchemy import text
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_db, get_current_user, require_role

router = APIRouter(prefix="/api/v1/suppliers", tags=["供应商管理"])


@router.get("/")
def list_suppliers(
    keyword: str = "",
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """供应商列表"""
    where = "WHERE 1=1"
    params = {}
    if keyword:
        where += " AND (name LIKE :kw OR contact_person LIKE :kw2 OR phone LIKE :kw3)"
        params["kw"] = f"%{keyword}%"
        params["kw2"] = f"%{keyword}%"
        params["kw3"] = f"%{keyword}%"

    total = conn.execute(text(f"SELECT COUNT(*) FROM suppliers {where}"), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = conn.execute(text(
        f"SELECT * FROM suppliers {where} ORDER BY id DESC LIMIT :limit OFFSET :offset"
    ), params).fetchall()
    return {"suppliers": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size}


@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: int,
    name: str = Query(default=None, max_length=200),
    contact_person: str = Query(default=None),
    phone: str = Query(default=None),
    email: str = Query(default=None),
    address: str = Query(default=None),
    notes: str = Query(default=None),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """更新供应商"""
    existing = conn.execute(text("SELECT id FROM suppliers WHERE id = :sid"), {"sid": supplier_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="供应商不存在")

    updates = {}
    for field in ["name", "contact_person", "phone", "email", "address", "notes"]:
        val = locals().get(field)
        if val is not None:
            updates[field] = val

    if updates:
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        params = dict(updates)
        params["sid"] = supplier_id
        conn.rollback()
        with conn.begin():
            conn.execute(text(
                f"UPDATE suppliers SET {set_clause}, updated_at = NOW() WHERE id = :sid"
            ), params)

    return {"message": "供应商更新成功"}


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """删除供应商"""
    existing = conn.execute(text("SELECT id FROM suppliers WHERE id = :sid"), {"sid": supplier_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="供应商不存在")
    conn.execute(text("DELETE FROM suppliers WHERE id = :sid"), {"sid": supplier_id})
    conn.commit()
    return {"message": "供应商已删除"}
