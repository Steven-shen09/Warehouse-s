"""消耗品领用管理路由"""
from sqlalchemy import text
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from app.api.deps import get_db, get_current_user, require_role
from app.services.consumable_service import (
    submit_consumable, submit_batch_consumable,
    approve_consumable, reject_consumable,
)

router = APIRouter(prefix="/api/v1/consumable-records", tags=["消耗品领用"])


@router.get("/")
def list_records(
    status: str = "",
    user_id: int = Query(default=None),
    document_no: str = "",
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """消耗品领用记录列表"""
    where = "WHERE 1=1"
    params = {}
    if status:
        where += " AND cr.status = :st"
        params["st"] = status
    if user_id is not None:
        where += " AND cr.user_id = :uid"
        params["uid"] = user_id
    if document_no:
        where += " AND cr.document_no LIKE :dn"
        params["dn"] = f"%{document_no}%"

    # 普通用户只看自己的
    if current_user["role"] == "user":
        where += " AND cr.user_id = :muid"
        params["muid"] = current_user["id"]

    total = conn.execute(text(
        f"SELECT COUNT(*) FROM consumable_records cr {where}"
    ), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = conn.execute(text(
        f"SELECT cr.*, i.name AS item_name, i.category, "
        f"u.display_name AS user_name, w.name AS warehouse_name "
        f"FROM consumable_records cr "
        f"JOIN items i ON cr.item_id = i.id "
        f"LEFT JOIN users u ON cr.user_id = u.id "
        f"LEFT JOIN warehouses w ON cr.source_warehouse_id = w.id "
        f"{where} ORDER BY cr.id DESC LIMIT :limit OFFSET :offset"
    ), params).fetchall()

    return {"records": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/")
def submit(
    item_id: int = Query(...),
    quantity: int = Query(..., ge=1),
    source_warehouse_id: int = Query(...),
    pickup_date: date = Query(default=None),
    reason: str = Query(default=""),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """提交消耗品领用申请"""
    if pickup_date is None:
        from datetime import date as dt_date
        pickup_date = dt_date.today()

    data = {
        "item_id": item_id, "quantity": quantity,
        "source_warehouse_id": source_warehouse_id,
        "pickup_date": pickup_date, "reason": reason,
    }
    conn.rollback()
    with conn.begin():
        try:
            result = submit_consumable(conn, data, current_user["id"], current_user["id"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "领用申请已提交", "document_no": result["document_no"]}


@router.post("/batch")
def submit_batch(
    items_json: str = Query(..., description="JSON格式的领用明细列表"),
    pickup_date: date = Query(default=None),
    reason: str = Query(default=""),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """批量提交消耗品领用申请"""
    import json
    try:
        items = json.loads(items_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="领用明细格式错误")

    if not items:
        raise HTTPException(status_code=400, detail="领用明细不能为空")

    if pickup_date is None:
        from datetime import date as dt_date
        pickup_date = dt_date.today()

    data = {"items": items, "pickup_date": pickup_date, "reason": reason}
    conn.rollback()
    with conn.begin():
        try:
            result = submit_batch_consumable(conn, data, current_user["id"], current_user["id"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "批量领用申请已提交", "document_no": result["document_no"]}


@router.put("/{record_id}/approve")
def approve(
    record_id: int,
    comment: str = Query(default=""),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """审核通过消耗品领用（永久扣减库存）"""
    conn.rollback()
    with conn.begin():
        try:
            approve_consumable(conn, record_id, current_user["id"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "领用审核通过，库存已扣减"}


@router.put("/{record_id}/reject")
def reject(
    record_id: int,
    comment: str = Query(..., min_length=1),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """驳回消耗品领用"""
    conn.rollback()
    with conn.begin():
        try:
            reject_consumable(conn, record_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "领用申请已驳回"}
