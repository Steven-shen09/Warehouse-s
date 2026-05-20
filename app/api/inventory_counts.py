"""盘点管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_db, get_current_user, require_role
from app.schemas.warehouse import InventoryCountCreate, InventoryCountItemUpdate

router = APIRouter(prefix="/api/v1/inventory-counts", tags=["盘点管理"])


@router.get("/")
def list_counts(
    page: int = 1,
    page_size: int = 20,
    status: str = "",
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """盘点列表"""
    where = "WHERE 1=1"
    params = []
    if status:
        where += " AND c.status = ?"
        params.append(status)

    total = conn.execute(f"SELECT COUNT(*) FROM inventory_counts c {where}", params).fetchone()[0]
    offset = (page - 1) * page_size

    rows = conn.execute(
        f"""SELECT c.*, w.name AS warehouse_name, u.display_name AS created_by_name
           FROM inventory_counts c
           JOIN warehouses w ON c.warehouse_id = w.id
           JOIN users u ON c.created_by = u.id
           {where} ORDER BY c.id DESC LIMIT ? OFFSET ?""",
        params + [page_size, offset],
    ).fetchall()

    return {
        "counts": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/")
def create_count(
    body: InventoryCountCreate,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """创建盘点 → 自动生成该仓库所有物品明细"""
    wh = conn.execute("SELECT id FROM warehouses WHERE id = ?", (body.warehouse_id,)).fetchone()
    if not wh:
        raise HTTPException(status_code=400, detail="仓库不存在")

    conn.execute(
        "INSERT INTO inventory_counts (warehouse_id, name, created_by) VALUES (?, ?, ?)",
        (body.warehouse_id, body.name, current_user["id"]),
    )
    count_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 自动生成该仓库所有物品的盘点明细
    stocks = conn.execute(
        """SELECT ws.item_id, ws.quantity AS stock_qty, i.name
           FROM warehouse_stocks ws JOIN items i ON ws.item_id = i.id
           WHERE ws.warehouse_id = ? AND ws.quantity > 0""",
        (body.warehouse_id,),
    ).fetchall()

    for s in stocks:
        conn.execute(
            "INSERT INTO inventory_count_items (count_id, item_id, expected_quantity) VALUES (?, ?, ?)",
            (count_id, s["item_id"], s["stock_qty"]),
        )

    conn.commit()
    return {"message": "盘点已创建", "count_id": count_id, "item_count": len(stocks)}


@router.get("/{count_id}")
def get_count(
    count_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """盘点详情（含明细列表）"""
    c = conn.execute(
        """SELECT c.*, w.name AS warehouse_name, u.display_name AS created_by_name
           FROM inventory_counts c
           JOIN warehouses w ON c.warehouse_id = w.id
           JOIN users u ON c.created_by = u.id
           WHERE c.id = ?""",
        (count_id,),
    ).fetchone()
    if not c:
        raise HTTPException(status_code=404, detail="盘点不存在")

    items = conn.execute(
        """SELECT ci.*, i.name AS item_name, i.category, i.location
           FROM inventory_count_items ci JOIN items i ON ci.item_id = i.id
           WHERE ci.count_id = ? ORDER BY ci.id""",
        (count_id,),
    ).fetchall()

    return {"count": dict(c), "items": [dict(r) for r in items]}


@router.put("/{count_id}/items/{item_id}")
def update_count_item(
    count_id: int,
    item_id: int,
    body: InventoryCountItemUpdate,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """录入实盘数量"""
    c = conn.execute(
        "SELECT id, status FROM inventory_counts WHERE id = ?", (count_id,)
    ).fetchone()
    if not c:
        raise HTTPException(status_code=404, detail="盘点不存在")
    if c["status"] != "进行中":
        raise HTTPException(status_code=400, detail="盘点已完成或已确认")

    ci = conn.execute(
        "SELECT id FROM inventory_count_items WHERE count_id = ? AND item_id = ?",
        (count_id, item_id),
    ).fetchone()
    if not ci:
        raise HTTPException(status_code=404, detail="盘点明细不存在")

    diff = None
    if body.actual_quantity is not None:
        expected = conn.execute(
            "SELECT expected_quantity FROM inventory_count_items WHERE count_id = ? AND item_id = ?",
            (count_id, item_id),
        ).fetchone()["expected_quantity"]
        diff = body.actual_quantity - expected

    conn.execute(
        """UPDATE inventory_count_items
           SET actual_quantity = ?, difference = ?, notes = ?, counted_at = datetime('now','localtime')
           WHERE count_id = ? AND item_id = ?""",
        (body.actual_quantity, diff, body.notes, count_id, item_id),
    )
    conn.commit()
    return {"message": "实盘数量已录入"}


@router.put("/{count_id}/complete")
def complete_count(
    count_id: int,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """完成盘点"""
    c = conn.execute(
        "SELECT id, status FROM inventory_counts WHERE id = ?", (count_id,)
    ).fetchone()
    if not c:
        raise HTTPException(status_code=404, detail="盘点不存在")
    if c["status"] != "进行中":
        raise HTTPException(status_code=400, detail="盘点已完成或已确认")

    conn.execute(
        "UPDATE inventory_counts SET status = '已完成', completed_at = datetime('now','localtime'), updated_at = datetime('now','localtime') WHERE id = ?",
        (count_id,),
    )
    conn.commit()
    return {"message": "盘点已完成"}


@router.put("/{count_id}/confirm")
def confirm_count(
    count_id: int,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """确认盘点差异 → 更新库存"""
    c = conn.execute(
        "SELECT id, status, warehouse_id FROM inventory_counts WHERE id = ?", (count_id,)
    ).fetchone()
    if not c:
        raise HTTPException(status_code=404, detail="盘点不存在")
    if c["status"] != "已完成":
        raise HTTPException(status_code=400, detail="请先完成盘点再确认")

    items = conn.execute(
        "SELECT item_id, actual_quantity, difference FROM inventory_count_items WHERE count_id = ?",
        (count_id,),
    ).fetchall()

    try:
        conn.execute("BEGIN IMMEDIATE")
        for item in items:
            if item["actual_quantity"] is not None:
                conn.execute(
                    """UPDATE warehouse_stocks SET quantity = ?
                       WHERE item_id = ? AND warehouse_id = ?""",
                    (item["actual_quantity"], item["item_id"], c["warehouse_id"]),
                )
                # 更新 total_quantity
                from app.api.transfers import _update_item_total
                _update_item_total(conn, item["item_id"])

        conn.execute(
            "UPDATE inventory_counts SET status = '已确认', updated_at = datetime('now','localtime') WHERE id = ?",
            (count_id,),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="盘点确认失败，已回滚")

    return {"message": "盘点已确认，库存已更新"}
