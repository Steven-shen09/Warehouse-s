"""资产报废管理路由"""
from sqlalchemy import text
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_db, get_current_user, require_role
from app.services.asset_service import create_disposal, approve_disposal, reject_disposal

router = APIRouter(prefix="/api/v1/asset-disposals", tags=["资产报废管理"])


@router.get("/")
def list_disposals(
    status: str = "",
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """报废单列表"""
    where = "WHERE 1=1"
    params = {}
    if status:
        where += " AND ad.status = :st"
        params["st"] = status

    total = conn.execute(text(
        f"SELECT COUNT(*) FROM asset_disposals ad {where}"
    ), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = conn.execute(text(
        f"SELECT ad.*, ai.asset_code, i.name AS item_name, "
        f"u.display_name AS created_by_name "
        f"FROM asset_disposals ad "
        f"JOIN asset_instances ai ON ad.asset_instance_id = ai.id "
        f"JOIN items i ON ai.item_id = i.id "
        f"LEFT JOIN users u ON ad.created_by = u.id "
        f"{where} ORDER BY ad.id DESC LIMIT :limit OFFSET :offset"
    ), params).fetchall()

    return {"disposals": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/")
def create(
    asset_instance_id: int = Query(...),
    disposal_type: str = Query(..., description="报废/出售/捐赠/丢失"),
    reason: str = Query(default=""),
    residual_value: float = Query(default=0.0, ge=0),
    notes: str = Query(default=""),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """创建报废申请"""
    data = {
        "asset_instance_id": asset_instance_id,
        "disposal_type": disposal_type,
        "reason": reason,
        "residual_value": residual_value,
        "notes": notes,
    }
    conn.rollback()
    with conn.begin():
        try:
            result = create_disposal(conn, data, current_user["id"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "报废申请已提交", "document_no": result["document_no"]}


@router.put("/{disposal_id}/approve")
def approve(
    disposal_id: int,
    comment: str = Query(default=""),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """审核通过报废"""
    conn.rollback()
    with conn.begin():
        try:
            approve_disposal(conn, disposal_id, current_user["id"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "报废申请已通过"}


@router.put("/{disposal_id}/reject")
def reject(
    disposal_id: int,
    comment: str = Query(..., min_length=1),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """驳回报废"""
    conn.rollback()
    with conn.begin():
        try:
            reject_disposal(conn, disposal_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "报废申请已驳回"}
