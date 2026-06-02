"""仓库管理路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from app.api.deps import get_db, get_current_user, require_role
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate

router = APIRouter(prefix="/api/v1/warehouses", tags=["仓库管理"])


@router.get("/")
def list_warehouses(
    page: int = 1,
    page_size: int = 12,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """仓库列表（分页）"""
    total = conn.execute(text("SELECT COUNT(*) FROM warehouses")).fetchone()[0]
    offset = (page - 1) * page_size
    rows = conn.execute(text(
        "SELECT * FROM warehouses ORDER BY id LIMIT :limit OFFSET :offset"
    ), {"limit": page_size, "offset": offset}).fetchall()
    return {
        "warehouses": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/")
def create_warehouse(
    body: WarehouseCreate,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """新增仓库"""
    conn.execute(text(
        "INSERT INTO warehouses (name, location, description) VALUES (:n, :loc, :desc)"
    ), {"n": body.name, "loc": body.location, "desc": body.description})
    conn.commit()
    return {"message": "仓库创建成功"}


@router.put("/{warehouse_id}")
def update_warehouse(
    warehouse_id: int,
    body: WarehouseUpdate,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """编辑仓库"""
    wh = conn.execute(text("SELECT id FROM warehouses WHERE id = :wid"), {"wid": warehouse_id}).fetchone()
    if not wh:
        raise HTTPException(status_code=404, detail="仓库不存在")

    updates = {}
    for field in ["name", "location", "description"]:
        val = getattr(body, field)
        if val is not None:
            updates[field] = val

    if updates:
        set_parts = []
        set_params = {}
        for field in ["name", "location", "description"]:
            val = getattr(body, field)
            if val is not None:
                set_parts.append(f"{field} = :{field}")
                set_params[field] = val
        set_params["wid"] = warehouse_id
        set_clause = ", ".join(set_parts)
        conn.execute(text(
            f"UPDATE warehouses SET {set_clause}, updated_at = NOW() WHERE id = :wid"
        ), set_params)
        conn.commit()

    return {"message": "仓库信息更新成功"}


@router.get("/{warehouse_id}/items")
def get_warehouse_items(
    warehouse_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """获取仓库内所有物品"""
    wh = conn.execute(text("SELECT id, name FROM warehouses WHERE id = :wid"), {"wid": warehouse_id}).fetchone()
    if not wh:
        raise HTTPException(status_code=404, detail="仓库不存在")

    rows = conn.execute(text(
        """SELECT i.id, i.name, i.category, i.description, i.status, i.value,
                  ws.quantity AS stock_quantity
           FROM warehouse_stocks ws
           JOIN items i ON ws.item_id = i.id
           WHERE ws.warehouse_id = :wid AND ws.quantity > 0
           ORDER BY i.name"""
    ), {"wid": warehouse_id}).fetchall()

    return {"warehouse": dict(wh), "items": [dict(r) for r in rows]}


@router.delete("/{warehouse_id}")
def delete_warehouse(
    warehouse_id: int,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """删除仓库（无物品库存时）"""
    wh = conn.execute(text("SELECT id FROM warehouses WHERE id = :wid"), {"wid": warehouse_id}).fetchone()
    if not wh:
        raise HTTPException(status_code=404, detail="仓库不存在")

    stock = conn.execute(text(
        "SELECT COALESCE(SUM(quantity), 0) FROM warehouse_stocks WHERE warehouse_id = :wid"
    ), {"wid": warehouse_id}).fetchone()[0]
    if stock and stock > 0:
        raise HTTPException(status_code=400, detail="该仓库中仍有物品库存，无法删除")

    conn.execute(text("DELETE FROM warehouses WHERE id = :wid"), {"wid": warehouse_id})
    conn.commit()
    return {"message": "仓库已删除"}
