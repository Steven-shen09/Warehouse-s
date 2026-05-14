"""审核路由"""
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_db, get_current_user, require_role
from app.schemas.approval import ApproveRequest, RejectRequest
from app.services.approval_service import approve, reject, get_pending_approvals, get_overdue_approvals_count

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
    total_pending = conn.execute("SELECT COUNT(*) FROM records WHERE status = '待审核'").fetchone()[0]
    total_overtime = get_overdue_approvals_count(conn)
    today_processed = conn.execute(
        "SELECT COUNT(*) FROM approvals WHERE date(created_at) = date('now','localtime')"
    ).fetchone()[0]
    return {
        "total_pending": total_pending,
        "total_overtime": total_overtime,
        "today_processed": today_processed,
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


@router.get("/{record_id}/history")
def approval_history(
    record_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """某记录的审核历史"""
    rows = conn.execute(
        """SELECT a.*, u.username as approver_username, u.display_name as approver_name
           FROM approvals a JOIN users u ON a.approver_id = u.id
           WHERE a.record_id = ? ORDER BY a.created_at DESC""",
        (record_id,),
    ).fetchall()
    return {"items": [dict(r) for r in rows]}
