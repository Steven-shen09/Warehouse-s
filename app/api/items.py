"""物品管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_db, get_current_user, require_role
from app.schemas.item import ItemCreate, ItemUpdate
from app.services.inventory_service import get_available_quantity, update_item_status

router = APIRouter(prefix="/api/v1/items", tags=["物品管理"])


@router.get("/")
def list_items(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    category: str = "",
    status: str = "",
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """物品列表（支持搜索、分类筛选、分页）"""
    where = "WHERE 1=1"
    params = []
    if keyword:
        where += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if category:
        where += " AND category = ?"
        params.append(category)
    if status:
        where += " AND status = ?"
        params.append(status)

    total = conn.execute(f"SELECT COUNT(*) FROM items {where}", params).fetchone()[0]
    offset = (page - 1) * page_size

    items = conn.execute(
        f"SELECT * FROM items {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [page_size, offset],
    ).fetchall()

    result = []
    for item in items:
        item_dict = dict(item)
        item_dict["available_quantity"] = get_available_quantity(conn, item["id"])
        result.append(item_dict)

    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.get("/categories")
def get_categories(
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """获取所有物品分类列表"""
    rows = conn.execute("SELECT DISTINCT category FROM items WHERE category != '' ORDER BY category").fetchall()
    return {"categories": [r["category"] for r in rows]}


@router.get("/{item_id}")
def get_item(
    item_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """获取物品详情（含实时库存）"""
    item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    item_dict = dict(item)
    item_dict["available_quantity"] = get_available_quantity(conn, item_id)
    return item_dict


@router.post("/")
def create_item(
    body: ItemCreate,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """新增物品"""
    conn.execute(
        """INSERT INTO items (name, category, description, location, total_quantity, value, low_stock_threshold, image_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (body.name, body.category, body.description, body.location,
         body.total_quantity, body.value, body.low_stock_threshold, body.image_url),
    )
    conn.commit()
    return {"message": "物品创建成功"}


@router.put("/{item_id}")
def update_item(
    item_id: int,
    body: ItemUpdate,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """更新物品信息"""
    item = conn.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")

    updates = {}
    for field in ["name", "category", "description", "location", "total_quantity", "value", "low_stock_threshold", "image_url"]:
        val = getattr(body, field)
        if val is not None:
            updates[field] = val

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [item_id]
        conn.execute(
            f"UPDATE items SET {set_clause}, updated_at = datetime('now','localtime') WHERE id = ?", values
        )
        conn.commit()
        # 更新库存状态
        update_item_status(conn, item_id)
        conn.commit()

    return {"message": "物品信息更新成功"}


@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """删除物品（前提：无活跃租借记录）"""
    active = conn.execute(
        "SELECT COUNT(*) FROM records WHERE item_id = ? AND status IN ('借出中', '逾期', '待审核')",
        (item_id,),
    ).fetchone()[0]
    if active > 0:
        raise HTTPException(status_code=400, detail="该物品存在活跃租借记录，无法删除")

    conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    return {"message": "物品已删除"}


@router.put("/{item_id}/mark-damaged")
def mark_damaged(
    item_id: int,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """标记物品为损坏"""
    item = conn.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    conn.execute("UPDATE items SET status = '损坏', updated_at = datetime('now','localtime') WHERE id = ?", (item_id,))
    conn.commit()
    return {"message": "物品已标记为损坏"}


@router.put("/{item_id}/mark-available")
def mark_available(
    item_id: int,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """恢复物品为可用"""
    item = conn.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    conn.execute("UPDATE items SET status = '可用', updated_at = datetime('now','localtime') WHERE id = ?", (item_id,))
    conn.commit()
    update_item_status(conn, item_id)
    conn.commit()
    return {"message": "物品已恢复为可用"}
