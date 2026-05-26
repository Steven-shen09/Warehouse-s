"""仓库物品浏览 API（按仓库类型筛选）"""
from sqlalchemy import text
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_db, get_current_user

router = APIRouter(prefix="/api/v1/warehouse-items", tags=["仓库物品"])


@router.get("/tools")
def list_tool_items(
    keyword: str = "",
    category: str = "",
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """工具仓库物品列表"""
    where = "WHERE i.item_type = 'tool'"
    params = {}
    if keyword:
        where += " AND i.name LIKE :kw"
        params["kw"] = f"%{keyword}%"
    if category:
        where += " AND i.category = :cat"
        params["cat"] = category

    total = conn.execute(text(
        f"SELECT COUNT(*) FROM items i {where}"
    ), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = conn.execute(text(
        f"SELECT i.id, i.name, i.category, i.description, i.specification, i.brand, "
        f"i.location, i.image_url, i.status, i.value, i.low_stock_threshold, "
        f"ws.warehouse_id, ws.quantity AS stock_quantity, w.name AS warehouse_name "
        f"FROM items i "
        f"LEFT JOIN warehouse_stocks ws ON i.id = ws.item_id "
        f"LEFT JOIN warehouses w ON ws.warehouse_id = w.id "
        f"{where} ORDER BY i.id DESC LIMIT :limit OFFSET :offset"
    ), params).fetchall()

    items = []
    for r in rows:
        d = dict(r)
        if current_user["role"] == "user":
            d.pop("value", None)
        items.append(d)

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/consumables")
def list_consumable_items(
    keyword: str = "",
    category: str = "",
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """耗材仓库物品列表"""
    where = "WHERE i.item_type = 'consumable'"
    params = {}
    if keyword:
        where += " AND i.name LIKE :kw"
        params["kw"] = f"%{keyword}%"
    if category:
        where += " AND i.category = :cat"
        params["cat"] = category

    total = conn.execute(text(
        f"SELECT COUNT(*) FROM items i {where}"
    ), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = conn.execute(text(
        f"SELECT i.id, i.name, i.category, i.description, i.specification, i.brand, "
        f"i.location, i.image_url, i.status, i.value, "
        f"ws.warehouse_id, ws.quantity AS stock_quantity, w.name AS warehouse_name "
        f"FROM items i "
        f"LEFT JOIN warehouse_stocks ws ON i.id = ws.item_id "
        f"LEFT JOIN warehouses w ON ws.warehouse_id = w.id "
        f"{where} ORDER BY i.id DESC LIMIT :limit OFFSET :offset"
    ), params).fetchall()

    items = []
    for r in rows:
        d = dict(r)
        if current_user["role"] == "user":
            d.pop("value", None)
        items.append(d)

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/assets")
def list_asset_instances(
    keyword: str = "",
    category: str = "",
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """固产仓库可领用资产列表（仅显示在库资产）"""
    where = "WHERE ai.status = '在库'"
    params = {}
    if keyword:
        where += " AND (i.name LIKE :kw OR ai.asset_code LIKE :kw)"
        params["kw"] = f"%{keyword}%"
    if category:
        where += " AND i.category = :cat"
        params["cat"] = category

    total = conn.execute(text(
        f"SELECT COUNT(*) FROM asset_instances ai JOIN items i ON ai.item_id = i.id {where}"
    ), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = conn.execute(text(
        f"SELECT ai.id, ai.asset_code, ai.serial_number, ai.purchase_date, ai.notes, "
        f"i.name AS item_name, i.category, i.description, i.specification, i.brand, i.value, "
        f"w.name AS warehouse_name "
        f"FROM asset_instances ai "
        f"JOIN items i ON ai.item_id = i.id "
        f"LEFT JOIN warehouses w ON ai.warehouse_id = w.id "
        f"{where} ORDER BY ai.id DESC LIMIT :limit OFFSET :offset"
    ), params).fetchall()

    assets = []
    for r in rows:
        d = dict(r)
        if current_user["role"] == "user":
            d.pop("value", None)
        assets.append(d)

    return {"assets": assets, "total": total, "page": page, "page_size": page_size}


@router.get("/categories")
def get_categories(
    item_type: str = Query(..., description="tool|consumable|fixed_asset"),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """获取某类型的物品分类列表"""
    rows = conn.execute(text(
        "SELECT DISTINCT category FROM items WHERE item_type = :it AND category != '' ORDER BY category"
    ), {"it": item_type}).fetchall()
    return {"categories": [r[0] for r in rows]}
