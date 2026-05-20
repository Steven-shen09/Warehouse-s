"""调拨管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_db, get_current_user, require_role
from app.schemas.warehouse import TransferCreate

router = APIRouter(prefix="/api/v1/transfers", tags=["调拨管理"])


def _generate_doc_no(conn) -> str:
    """生成调拨单号 DB-YYYYMMDD-XXX"""
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    count = conn.execute(
        "SELECT COUNT(*) FROM transfers WHERE document_no LIKE ?",
        (f"DB-{today}-%",),
    ).fetchone()[0]
    return f"DB-{today}-{count + 1:03d}"


@router.get("/")
def list_transfers(
    page: int = 1,
    page_size: int = 20,
    status: str = "",
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """调拨记录列表"""
    where = "WHERE 1=1"
    params = []
    if status:
        where += " AND t.status = ?"
        params.append(status)

    total = conn.execute(f"SELECT COUNT(*) FROM transfers t {where}", params).fetchone()[0]
    offset = (page - 1) * page_size

    rows = conn.execute(
        f"""SELECT t.*, i.name AS item_name,
           fw.name AS from_warehouse_name, tw.name AS to_warehouse_name,
           cu.display_name AS created_by_name, au.display_name AS approved_by_name
           FROM transfers t
           JOIN items i ON t.item_id = i.id
           JOIN warehouses fw ON t.from_warehouse_id = fw.id
           JOIN warehouses tw ON t.to_warehouse_id = tw.id
           JOIN users cu ON t.created_by = cu.id
           LEFT JOIN users au ON t.approved_by = au.id
           {where} ORDER BY t.id DESC LIMIT ? OFFSET ?""",
        params + [page_size, offset],
    ).fetchall()

    return {
        "transfers": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/")
def create_transfer(
    body: TransferCreate,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """创建调拨申请"""
    if body.from_warehouse_id == body.to_warehouse_id:
        raise HTTPException(status_code=400, detail="源仓库和目标仓库不能相同")

    item = conn.execute("SELECT id, name FROM items WHERE id = ?", (body.item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=400, detail="物品不存在")

    from_wh = conn.execute("SELECT id FROM warehouses WHERE id = ?", (body.from_warehouse_id,)).fetchone()
    to_wh = conn.execute("SELECT id FROM warehouses WHERE id = ?", (body.to_warehouse_id,)).fetchone()
    if not from_wh or not to_wh:
        raise HTTPException(status_code=400, detail="仓库不存在")

    stock = conn.execute(
        "SELECT quantity FROM warehouse_stocks WHERE item_id = ? AND warehouse_id = ?",
        (body.item_id, body.from_warehouse_id),
    ).fetchone()
    available = stock["quantity"] if stock else 0
    if available < body.quantity:
        raise HTTPException(status_code=400, detail=f"源仓库库存不足（可用：{available}，需要：{body.quantity}）")

    doc_no = _generate_doc_no(conn)
    conn.execute(
        """INSERT INTO transfers (item_id, from_warehouse_id, to_warehouse_id, quantity, reason, document_no, created_by)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (body.item_id, body.from_warehouse_id, body.to_warehouse_id, body.quantity, body.reason, doc_no, current_user["id"]),
    )
    conn.commit()
    return {"message": "调拨申请已创建", "document_no": doc_no}


@router.put("/{transfer_id}/approve")
def approve_transfer(
    transfer_id: int,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """审核通过 → 执行库存调拨"""
    t = conn.execute("SELECT * FROM transfers WHERE id = ?", (transfer_id,)).fetchone()
    if not t:
        raise HTTPException(status_code=404, detail="调拨记录不存在")
    if t["status"] != "待审核":
        raise HTTPException(status_code=400, detail="该调拨记录已处理")

    # 再次校验库存
    stock = conn.execute(
        "SELECT quantity FROM warehouse_stocks WHERE item_id = ? AND warehouse_id = ?",
        (t["item_id"], t["from_warehouse_id"]),
    ).fetchone()
    available = stock["quantity"] if stock else 0
    if available < t["quantity"]:
        raise HTTPException(status_code=400, detail=f"源仓库库存不足（当前可用：{available}）")

    try:
        conn.execute("BEGIN IMMEDIATE")
        # 扣减源仓库
        conn.execute(
            "UPDATE warehouse_stocks SET quantity = quantity - ? WHERE item_id = ? AND warehouse_id = ?",
            (t["quantity"], t["item_id"], t["from_warehouse_id"]),
        )
        # 增加目标仓库
        existing = conn.execute(
            "SELECT id FROM warehouse_stocks WHERE item_id = ? AND warehouse_id = ?",
            (t["item_id"], t["to_warehouse_id"]),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE warehouse_stocks SET quantity = quantity + ? WHERE item_id = ? AND warehouse_id = ?",
                (t["quantity"], t["item_id"], t["to_warehouse_id"]),
            )
        else:
            conn.execute(
                "INSERT INTO warehouse_stocks (item_id, warehouse_id, quantity) VALUES (?, ?, ?)",
                (t["item_id"], t["to_warehouse_id"], t["quantity"]),
            )
        # 更新调拨状态
        conn.execute(
            "UPDATE transfers SET status = '已通过', approved_by = ?, updated_at = datetime('now','localtime') WHERE id = ?",
            (current_user["id"], transfer_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="调拨执行失败，已回滚")

    # 更新物品 total_quantity
    _update_item_total(conn, t["item_id"])
    conn.commit()

    return {"message": "调拨已通过，库存已转移"}


@router.put("/{transfer_id}/reject")
def reject_transfer(
    transfer_id: int,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """驳回调拨"""
    t = conn.execute("SELECT * FROM transfers WHERE id = ?", (transfer_id,)).fetchone()
    if not t:
        raise HTTPException(status_code=404, detail="调拨记录不存在")
    if t["status"] != "待审核":
        raise HTTPException(status_code=400, detail="该调拨记录已处理")

    conn.execute(
        "UPDATE transfers SET status = '已驳回', approved_by = ?, updated_at = datetime('now','localtime') WHERE id = ?",
        (current_user["id"], transfer_id),
    )
    conn.commit()
    return {"message": "调拨已驳回"}


def _update_item_total(conn, item_id: int):
    """更新 items.total_quantity = 所有仓库库存之和"""
    total = conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) FROM warehouse_stocks WHERE item_id = ?", (item_id,)
    ).fetchone()[0]
    conn.execute(
        "UPDATE items SET total_quantity = ?, updated_at = datetime('now','localtime') WHERE id = ?",
        (total, item_id),
    )
