"""仓库管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_db, get_current_user, require_role
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate

router = APIRouter(prefix="/api/v1/warehouses", tags=["仓库管理"])


@router.get("/")
def list_warehouses(
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """仓库列表"""
    rows = conn.execute("SELECT * FROM warehouses ORDER BY id").fetchall()
    return {"warehouses": [dict(r) for r in rows]}


@router.post("/")
def create_warehouse(
    body: WarehouseCreate,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """新增仓库"""
    conn.execute(
        "INSERT INTO warehouses (name, location, description) VALUES (?, ?, ?)",
        (body.name, body.location, body.description),
    )
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
    wh = conn.execute("SELECT id FROM warehouses WHERE id = ?", (warehouse_id,)).fetchone()
    if not wh:
        raise HTTPException(status_code=404, detail="仓库不存在")

    updates = {}
    for field in ["name", "location", "description"]:
        val = getattr(body, field)
        if val is not None:
            updates[field] = val

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [warehouse_id]
        conn.execute(
            f"UPDATE warehouses SET {set_clause}, updated_at = datetime('now','localtime') WHERE id = ?", values
        )
        conn.commit()

    return {"message": "仓库信息更新成功"}


@router.delete("/{warehouse_id}")
def delete_warehouse(
    warehouse_id: int,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """删除仓库（无物品库存时）"""
    wh = conn.execute("SELECT id FROM warehouses WHERE id = ?", (warehouse_id,)).fetchone()
    if not wh:
        raise HTTPException(status_code=404, detail="仓库不存在")

    stock = conn.execute(
        "SELECT SUM(quantity) FROM warehouse_stocks WHERE warehouse_id = ?", (warehouse_id,)
    ).fetchone()[0]
    if stock and stock > 0:
        raise HTTPException(status_code=400, detail="该仓库中仍有物品库存，无法删除")

    conn.execute("DELETE FROM warehouses WHERE id = ?", (warehouse_id,))
    conn.commit()
    return {"message": "仓库已删除"}
