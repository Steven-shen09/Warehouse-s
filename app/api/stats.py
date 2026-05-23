"""统计路由"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
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
    total_items = conn.execute(text("SELECT COUNT(*) FROM items")).fetchone()[0]
    total_available = conn.execute(text(
        "SELECT COUNT(*) FROM items WHERE status = '可用'"
    )).fetchone()[0]
    total_quantity = conn.execute(text(
        "SELECT COALESCE(SUM(total_quantity), 0) FROM items"
    )).fetchone()[0]

    # 分类统计
    category_count = conn.execute(text(
        "SELECT COUNT(DISTINCT category) FROM items WHERE category != ''"
    )).fetchone()[0]
    cat_rows = conn.execute(text(
        "SELECT category, COUNT(*) as cnt FROM items WHERE category != '' GROUP BY category ORDER BY cnt DESC"
    )).fetchall()
    category_distribution = [{"name": r[0], "count": r[1]} for r in cat_rows]
    # 各分类库存总量占比
    cat_qty_rows = conn.execute(text(
        "SELECT category, COALESCE(SUM(total_quantity), 0) as total FROM items WHERE category != '' GROUP BY category ORDER BY total DESC"
    )).fetchall()
    category_quantity_distribution = [{"name": r[0], "count": r[1]} for r in cat_qty_rows]

    # 物品状态分布
    status_rows = conn.execute(text(
        "SELECT status, COUNT(*) as cnt FROM items GROUP BY status"
    )).fetchall()
    status_distribution = [{"status": r[0], "count": r[1]} for r in status_rows]

    # 仓库库存分布
    wh_rows = conn.execute(text(
        "SELECT w.name, COALESCE(SUM(ws.quantity), 0) as total FROM warehouses w LEFT JOIN warehouse_stocks ws ON w.id = ws.warehouse_id GROUP BY w.id ORDER BY w.id"
    )).fetchall()
    warehouse_distribution = [{"name": r[0], "count": r[1]} for r in wh_rows if r[1] > 0]

    # 记录指标 — 普通用户只显示自己的
    if is_user:
        total_borrowed = conn.execute(text(
            "SELECT COUNT(*) FROM records WHERE status IN ('借出中', '逾期') AND borrower_id = :uid"
        ), {"uid": user_id}).fetchone()[0]
        total_overdue = conn.execute(text(
            "SELECT COUNT(*) FROM records WHERE status = '逾期' AND borrower_id = :uid"
        ), {"uid": user_id}).fetchone()[0]
        total_pending = conn.execute(text(
            "SELECT COUNT(*) FROM records WHERE status = '待审核' AND borrower_id = :uid"
        ), {"uid": user_id}).fetchone()[0]
        returned_today = conn.execute(text(
            "SELECT COUNT(*) FROM records WHERE status = '已归还' AND date(updated_at) = CURRENT_DATE AND borrower_id = :uid"
        ), {"uid": user_id}).fetchone()[0]
        approval_timeout = conn.execute(text(
            "SELECT COUNT(*) FROM records WHERE status = '待审核' AND approval_deadline < NOW() AND borrower_id = :uid"
        ), {"uid": user_id}).fetchone()[0]
        low_stock_list = []
    else:
        total_borrowed = conn.execute(text(
            "SELECT COUNT(*) FROM records WHERE status IN ('借出中', '逾期')"
        )).fetchone()[0]
        total_overdue = conn.execute(text(
            "SELECT COUNT(*) FROM records WHERE status = '逾期'"
        )).fetchone()[0]
        total_pending = conn.execute(text(
            "SELECT COUNT(*) FROM records WHERE status = '待审核'"
        )).fetchone()[0]
        returned_today = conn.execute(text(
            "SELECT COUNT(*) FROM records WHERE status = '已归还' AND date(updated_at) = CURRENT_DATE"
        )).fetchone()[0]
        approval_timeout = conn.execute(text(
            "SELECT COUNT(*) FROM records WHERE status = '待审核' AND approval_deadline < NOW()"
        )).fetchone()[0]
        low_stock_list = check_low_stock(conn)

    return {
        "total_items": total_items,
        "total_borrowed": total_borrowed,
        "total_available": total_available,
        "total_quantity": total_quantity,
        "category_count": category_count,
        "category_distribution": category_distribution,
        "category_quantity_distribution": category_quantity_distribution,
        "warehouse_distribution": warehouse_distribution,
        "status_distribution": status_distribution,
        "total_overdue": total_overdue,
        "total_pending_approval": total_pending,
        "total_returned_today": returned_today,
        "low_stock_count": len(low_stock_list),
        "low_stock_items": low_stock_list,
        "approval_timeout_count": approval_timeout,
    }


@router.get("/weekly-trends")
def weekly_trends(
    weeks: int = Query(default=6, ge=2, le=52),
    start_date: str = Query(default=None),
    end_date: str = Query(default=None),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """返回趋势数据。支持按周数快捷查询或自定义日期范围（按日聚合）"""
    is_user = current_user["role"] == "user"
    user_id = current_user["id"]
    today = datetime.now()
    trends = []

    if start_date and end_date:
        # 自定义日期范围 — 按日聚合
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            ed = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return {"weeks": [], "error": "日期格式无效，需要 YYYY-MM-DD"}

        if sd > ed:
            sd, ed = ed, sd

        delta = (ed - sd).days
        if delta > 365:
            delta = 365
            ed = sd + timedelta(days=365)

        for i in range(delta, -1, -1):
            d = ed - timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            label = f"{d.month}/{d.day}"
            next_str = (d + timedelta(days=1)).strftime("%Y-%m-%d")

            if is_user:
                borrowed = conn.execute(text(
                    "SELECT COUNT(*) FROM records WHERE date(borrow_date) = :d_str AND borrower_id = :uid"
                ), {"d_str": d_str, "uid": user_id}).fetchone()[0]
                returned = conn.execute(text(
                    "SELECT COUNT(*) FROM records WHERE status = '已归还' AND date(updated_at) = :d_str AND borrower_id = :uid"
                ), {"d_str": d_str, "uid": user_id}).fetchone()[0]
            else:
                borrowed = conn.execute(text(
                    "SELECT COUNT(*) FROM records WHERE date(borrow_date) = :d_str"
                ), {"d_str": d_str}).fetchone()[0]
                returned = conn.execute(text(
                    "SELECT COUNT(*) FROM records WHERE status = '已归还' AND date(updated_at) = :d_str"
                ), {"d_str": d_str}).fetchone()[0]

            new_items = conn.execute(text(
                "SELECT COUNT(*) FROM items WHERE date(created_at) = :d_str"
            ), {"d_str": d_str}).fetchone()[0]

            trends.append({
                "label": label,
                "borrowed": borrowed,
                "returned": returned,
                "new_items": new_items,
            })
    else:
        # 按周聚合（原有逻辑）
        for i in range(weeks - 1, -1, -1):
            week_end = today - timedelta(days=i * 7)
            week_start = week_end - timedelta(days=6)
            label = f"{week_start.month}/{week_start.day}-{week_end.month}/{week_end.day}"
            start_str = week_start.strftime("%Y-%m-%d")
            end_str = week_end.strftime("%Y-%m-%d")

            if is_user:
                borrowed = conn.execute(text(
                    "SELECT COUNT(*) FROM records WHERE date(borrow_date) BETWEEN :start AND :end AND borrower_id = :uid"
                ), {"start": start_str, "end": end_str, "uid": user_id}).fetchone()[0]
                returned = conn.execute(text(
                    "SELECT COUNT(*) FROM records WHERE status = '已归还' AND date(updated_at) BETWEEN :start AND :end AND borrower_id = :uid"
                ), {"start": start_str, "end": end_str, "uid": user_id}).fetchone()[0]
            else:
                borrowed = conn.execute(text(
                    "SELECT COUNT(*) FROM records WHERE date(borrow_date) BETWEEN :start AND :end"
                ), {"start": start_str, "end": end_str}).fetchone()[0]
                returned = conn.execute(text(
                    "SELECT COUNT(*) FROM records WHERE status = '已归还' AND date(updated_at) BETWEEN :start AND :end"
                ), {"start": start_str, "end": end_str}).fetchone()[0]

            new_items = conn.execute(text(
                "SELECT COUNT(*) FROM items WHERE date(created_at) BETWEEN :start AND :end"
            ), {"start": start_str, "end": end_str}).fetchone()[0]

            trends.append({
                "label": label,
                "borrowed": borrowed,
                "returned": returned,
                "new_items": new_items,
            })

    return {"weeks": trends}


@router.get("/top-borrowed")
def top_borrowed(
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=7, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """返回最近 N 天借出次数最多的物品"""
    is_user = current_user["role"] == "user"
    user_id = current_user["id"]
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    if is_user:
        rows = conn.execute(text(
            """SELECT i.name, COUNT(*) as cnt, COALESCE(SUM(r.quantity), 0) as total_qty FROM records r
               JOIN items i ON r.item_id = i.id
               WHERE date(r.borrow_date) >= :since AND r.borrower_id = :uid
               GROUP BY r.item_id, i.name ORDER BY cnt DESC LIMIT :limit"""
        ), {"since": since, "uid": user_id, "limit": limit}).fetchall()
    else:
        rows = conn.execute(text(
            """SELECT i.name, COUNT(*) as cnt, COALESCE(SUM(r.quantity), 0) as total_qty FROM records r
               JOIN items i ON r.item_id = i.id
               WHERE date(r.borrow_date) >= :since
               GROUP BY r.item_id, i.name ORDER BY cnt DESC LIMIT :limit"""
        ), {"since": since, "limit": limit}).fetchall()

    return {"items": [{"name": r[0], "count": r[1], "total_qty": r[2]} for r in rows]}
