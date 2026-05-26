"""采购入库管理路由"""
from typing import Optional
from sqlalchemy import text
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import date
from app.api.deps import get_db, get_current_user, require_role
from app.services.purchase_service import create_purchase_order, approve_purchase_order, cancel_purchase_order

router = APIRouter(prefix="/api/v1/purchase-orders", tags=["采购入库"])


class POItemCreate(BaseModel):
    item_id: int
    quantity: int = Field(ge=1)
    unit_price: float = Field(default=0.0, ge=0)
    batch_no: str = Field(default="")
    production_date: Optional[date] = None
    expiry_date: Optional[date] = None
    notes: str = Field(default="")


class POCreateRequest(BaseModel):
    supplier_id: int
    warehouse_id: int
    purchase_date: date
    notes: str = Field(default="")
    items: list[POItemCreate]


@router.get("/")
def list_purchase_orders(
    status: str = "",
    supplier_id: int = Query(default=None),
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """采购单列表"""
    where = "WHERE 1=1"
    params = {}
    if status:
        where += " AND po.status = :st"
        params["st"] = status
    if supplier_id is not None:
        where += " AND po.supplier_id = :sid"
        params["sid"] = supplier_id

    total = conn.execute(text(
        f"SELECT COUNT(*) FROM purchase_orders po {where}"
    ), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = conn.execute(text(
        f"SELECT po.*, s.name AS supplier_name, w.name AS warehouse_name "
        f"FROM purchase_orders po "
        f"LEFT JOIN suppliers s ON po.supplier_id = s.id "
        f"LEFT JOIN warehouses w ON po.warehouse_id = w.id "
        f"{where} ORDER BY po.id DESC LIMIT :limit OFFSET :offset"
    ), params).fetchall()

    orders = []
    for row in rows:
        d = dict(row)
        items = conn.execute(text(
            "SELECT poi.*, i.name AS item_name, i.item_type FROM purchase_order_items poi "
            "JOIN items i ON poi.item_id = i.id WHERE poi.purchase_order_id = :pid"
        ), {"pid": d["id"]}).fetchall()
        d["items"] = [dict(it) for it in items]
        orders.append(d)

    return {"orders": orders, "total": total, "page": page, "page_size": page_size}


@router.get("/{order_id}")
def get_purchase_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """采购单详情"""
    po = conn.execute(text(
        "SELECT po.*, s.name AS supplier_name, w.name AS warehouse_name "
        "FROM purchase_orders po "
        "LEFT JOIN suppliers s ON po.supplier_id = s.id "
        "LEFT JOIN warehouses w ON po.warehouse_id = w.id "
        "WHERE po.id = :pid"
    ), {"pid": order_id}).fetchone()
    if not po:
        raise HTTPException(status_code=404, detail="采购单不存在")
    d = dict(po)
    items = conn.execute(text(
        "SELECT poi.*, i.name AS item_name, i.item_type FROM purchase_order_items poi "
        "JOIN items i ON poi.item_id = i.id WHERE poi.purchase_order_id = :pid"
    ), {"pid": order_id}).fetchall()
    d["items"] = [dict(it) for it in items]
    return d


@router.post("/")
def create_po(
    body: POCreateRequest,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """创建采购入库单"""
    conn.rollback()
    with conn.begin():
        result = create_purchase_order(conn, body.model_dump(), current_user["id"])
    return {"message": "采购单创建成功", "document_no": result["document_no"]}


@router.put("/{order_id}/approve")
def approve_po(
    order_id: int,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """审核通过采购单（执行入库）"""
    conn.rollback()
    with conn.begin():
        try:
            approve_purchase_order(conn, order_id, current_user["id"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "采购单已入库"}


@router.put("/{order_id}/cancel")
def cancel_po(
    order_id: int,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """取消采购单"""
    conn.rollback()
    with conn.begin():
        try:
            cancel_purchase_order(conn, order_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "采购单已取消"}
