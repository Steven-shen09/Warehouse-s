"""统计路由"""
from fastapi import APIRouter, Depends
from app.api.deps import get_db, get_current_user
from app.services.inventory_service import check_low_stock

router = APIRouter(prefix="/api/v1/stats", tags=["统计"])


@router.get("/")
def dashboard_stats(
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """仪表盘统计数据（普通用户仅显示与自己相关的记录统计）"""
    is_user = current_user["role"] == "user"
    user_id = current_user["id"]

    # 库存指标 — 所有人可见
    total_items = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    total_available = conn.execute(
        "SELECT COUNT(*) FROM items WHERE status = '可用'"
    ).fetchone()[0]

    # 记录指标 — 普通用户只显示自己的
    if is_user:
        total_borrowed = conn.execute(
            "SELECT COUNT(*) FROM records WHERE status IN ('借出中', '逾期') AND borrower_id = ?",
            (user_id,),
        ).fetchone()[0]
        total_overdue = conn.execute(
            "SELECT COUNT(*) FROM records WHERE status = '逾期' AND borrower_id = ?",
            (user_id,),
        ).fetchone()[0]
        total_pending = conn.execute(
            "SELECT COUNT(*) FROM records WHERE status = '待审核' AND borrower_id = ?",
            (user_id,),
        ).fetchone()[0]
        returned_today = conn.execute(
            "SELECT COUNT(*) FROM records WHERE status = '已归还' AND date(updated_at) = date('now','localtime') AND borrower_id = ?",
            (user_id,),
        ).fetchone()[0]
        approval_timeout = conn.execute(
            "SELECT COUNT(*) FROM records WHERE status = '待审核' AND approval_deadline < datetime('now','localtime') AND borrower_id = ?",
            (user_id,),
        ).fetchone()[0]
        low_stock_list = []
    else:
        total_borrowed = conn.execute(
            "SELECT COUNT(*) FROM records WHERE status IN ('借出中', '逾期')"
        ).fetchone()[0]
        total_overdue = conn.execute(
            "SELECT COUNT(*) FROM records WHERE status = '逾期'"
        ).fetchone()[0]
        total_pending = conn.execute(
            "SELECT COUNT(*) FROM records WHERE status = '待审核'"
        ).fetchone()[0]
        returned_today = conn.execute(
            "SELECT COUNT(*) FROM records WHERE status = '已归还' AND date(updated_at) = date('now','localtime')"
        ).fetchone()[0]
        approval_timeout = conn.execute(
            "SELECT COUNT(*) FROM records WHERE status = '待审核' AND approval_deadline < datetime('now','localtime')"
        ).fetchone()[0]
        low_stock_list = check_low_stock(conn)

    return {
        "total_items": total_items,
        "total_borrowed": total_borrowed,
        "total_available": total_available,
        "total_overdue": total_overdue,
        "total_pending_approval": total_pending,
        "total_returned_today": returned_today,
        "low_stock_count": len(low_stock_list),
        "low_stock_items": low_stock_list,
        "approval_timeout_count": approval_timeout,
    }
