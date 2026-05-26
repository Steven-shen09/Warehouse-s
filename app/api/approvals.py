"""审核路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from app.api.deps import get_db, get_current_user, require_role
from app.schemas.approval import ApproveRequest, RejectRequest
from app.services.approval_service import (
    approve, reject, get_pending_approvals, get_overdue_approvals_count,
    approve_by_document, reject_by_document, get_pending_approvals_grouped,
)
from app.services.asset_service import approve_assignment, reject_assignment

router = APIRouter(prefix="/api/v1/approvals", tags=["审核管理"])


@router.get("/pending")
def list_pending(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """待审核记录列表"""
    return get_pending_approvals(conn, page, page_size)


@router.get("/stats")
def approval_stats(
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """审核统计数据"""
    total_pending = conn.execute(text("SELECT COUNT(*) FROM records WHERE status = '待审核'")).fetchone()[0]
    transfer_pending = conn.execute(text("SELECT COUNT(*) FROM transfers WHERE status = '待审核'")).fetchone()[0]
    consumable_pending = conn.execute(text(
        "SELECT COUNT(*) FROM consumable_records WHERE status = '待审核'"
    )).fetchone()[0]
    asset_pending = conn.execute(text(
        "SELECT COUNT(*) FROM asset_assignments WHERE status = '待审核'"
    )).fetchone()[0]
    total_overtime = get_overdue_approvals_count(conn)
    today_processed = conn.execute(text(
        "SELECT COUNT(*) FROM approvals WHERE date(created_at) = CURRENT_DATE"
    )).fetchone()[0]
    to_return = conn.execute(text(
        "SELECT COUNT(*) FROM records WHERE status IN ('借出中', '逾期')"
    )).fetchone()[0]
    return {
        "total_pending": total_pending,
        "transfer_pending": transfer_pending,
        "consumable_pending": consumable_pending,
        "asset_pending": asset_pending,
        "total_overtime": total_overtime,
        "today_processed": today_processed,
        "to_return": to_return,
    }


@router.put("/{record_id}/approve")
def approve_record(
    record_id: int,
    body: ApproveRequest = ApproveRequest(),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """审核通过"""
    try:
        result = approve(
            conn,
            record_id=record_id,
            approver_id=current_user["id"],
            approver_name=current_user["display_name"] or current_user["username"],
            comment=body.comment,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{record_id}/reject")
def reject_record(
    record_id: int,
    body: RejectRequest,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """审核驳回"""
    try:
        result = reject(
            conn,
            record_id=record_id,
            approver_id=current_user["id"],
            approver_name=current_user["display_name"] or current_user["username"],
            comment=body.comment,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pending-grouped")
def list_pending_grouped(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """待审核记录列表（按单据号分组）"""
    return get_pending_approvals_grouped(conn, page, page_size)


@router.put("/by-document/{document_no}/approve")
def approve_document(
    document_no: str,
    body: ApproveRequest = ApproveRequest(),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """按单据号批量审核通过"""
    try:
        result = approve_by_document(
            conn,
            document_no=document_no,
            approver_id=current_user["id"],
            approver_name=current_user["display_name"] or current_user["username"],
            comment=body.comment,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/by-document/{document_no}/reject")
def reject_document(
    document_no: str,
    body: RejectRequest,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """按单据号批量驳回"""
    try:
        result = reject_by_document(
            conn,
            document_no=document_no,
            approver_id=current_user["id"],
            approver_name=current_user["display_name"] or current_user["username"],
            comment=body.comment,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{record_id}/history")
def approval_history(
    record_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """某记录的审核历史"""
    rows = conn.execute(text(
        """SELECT a.*, u.username as approver_username, u.display_name as approver_name
           FROM approvals a JOIN users u ON a.approver_id = u.id
           WHERE a.record_id = :rid ORDER BY a.created_at DESC"""
    ), {"rid": record_id}).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.get("/pending-transfers")
def list_pending_transfers(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """待审核调拨记录（按单据号分组）"""
    rows = conn.execute(text(
        """SELECT t.*, i.name AS item_name,
           fw.name AS from_warehouse_name, tw.name AS to_warehouse_name,
           cu.display_name AS created_by_name
           FROM transfers t
           JOIN items i ON t.item_id = i.id
           JOIN warehouses fw ON t.from_warehouse_id = fw.id
           JOIN warehouses tw ON t.to_warehouse_id = tw.id
           JOIN users cu ON t.created_by = cu.id
           WHERE t.status = '待审核'
           ORDER BY t.id DESC"""
    )).fetchall()

    transfers = []
    for r in rows:
        d = dict(r)
        d["status"] = "pending"
        transfers.append(d)

    # Group by document_no
    groups = {}
    for t in transfers:
        key = t.get("document_no") or f"DB-{t['id']}"
        if key not in groups:
            groups[key] = {
                "document_no": key,
                "type": "transfer",
                "from_warehouse_name": t["from_warehouse_name"],
                "to_warehouse_name": t["to_warehouse_name"],
                "created_by_name": t["created_by_name"],
                "created_at": t["created_at"],
                "items": [],
                "count": 0,
            }
        groups[key]["items"].append(t)
        groups[key]["count"] += 1

    all_groups = list(groups.values())
    total = len(all_groups)
    offset = (page - 1) * page_size
    paged = all_groups[offset:offset + page_size]

    return {"groups": paged, "total": total, "page": page, "page_size": page_size}


@router.get("/pending-assignments")
def list_pending_assignments(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """待审核固产领用列表"""
    total = conn.execute(text(
        "SELECT COUNT(*) FROM asset_assignments WHERE status = '待审核'"
    )).fetchone()[0]
    offset = (page - 1) * page_size

    rows = conn.execute(text(
        "SELECT aa.*, ai.asset_code, i.name AS item_name, i.specification, i.brand, "
        "u.display_name AS user_name, d.name AS department_name "
        "FROM asset_assignments aa "
        "JOIN asset_instances ai ON aa.asset_instance_id = ai.id "
        "JOIN items i ON ai.item_id = i.id "
        "LEFT JOIN users u ON aa.assigned_to_user_id = u.id "
        "LEFT JOIN departments d ON aa.assigned_to_department_id = d.id "
        "WHERE aa.status = '待审核' ORDER BY aa.id DESC LIMIT :limit OFFSET :offset"
    ), {"limit": page_size, "offset": offset}).fetchall()

    return {"assignments": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size}


@router.put("/assignments/{assignment_id}/approve")
def approve_assignment_endpoint(
    assignment_id: int,
    comment: str = Query(default=""),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """审核通过固产领用"""
    conn.rollback()
    with conn.begin():
        try:
            approve_assignment(conn, assignment_id, current_user["id"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "固产领用审核通过"}


@router.put("/assignments/{assignment_id}/reject")
def reject_assignment_endpoint(
    assignment_id: int,
    comment: str = Query(..., min_length=1),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """驳回固产领用"""
    conn.rollback()
    with conn.begin():
        try:
            reject_assignment(conn, assignment_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "固产领用已驳回"}
