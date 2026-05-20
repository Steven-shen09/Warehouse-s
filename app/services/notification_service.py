"""通知服务：审核提醒、归还提醒、异常告警"""
import sqlite3
from datetime import datetime, timedelta
from app.adapters.sms_adapter import AliyunSMSAdapter
from app.adapters.null_adapter import NullSMSAdapter
from app.config import settings
from app.services.inventory_service import update_item_status


def _get_sms_adapter():
    """获取 SMS 适配器：有配置则用阿里云，否则用空适配器"""
    if settings.SMS_ACCESS_KEY_ID:
        return AliyunSMSAdapter()
    return NullSMSAdapter()


def check_overdue_approvals(conn: sqlite3.Connection) -> list:
    """
    检查超时未审核的记录。
    返回超时记录列表。
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = conn.execute(
        """SELECT r.id, r.item_id, r.borrower_name, r.approval_deadline,
                  i.name as item_name
           FROM records r JOIN items i ON r.item_id = i.id
           WHERE r.status = '待审核' AND r.approval_deadline < ?""",
        (now,),
    ).fetchall()
    return [dict(r) for r in rows]


def check_upcoming_returns(conn: sqlite3.Connection, days_before: int = 1) -> list:
    """
    检查即将到期的租借记录。
    默认检查 1 天后到期的记录。
    """
    target_date = (datetime.now() + timedelta(days=days_before)).strftime("%Y-%m-%d")
    rows = conn.execute(
        """SELECT r.id, r.item_id, r.borrower_name, r.expected_return_date,
                  i.name as item_name
           FROM records r JOIN items i ON r.item_id = i.id
           WHERE r.status = '借出中' AND r.expected_return_date = ?""",
        (target_date,),
    ).fetchall()
    return [dict(r) for r in rows]


def check_overdue_records(conn: sqlite3.Connection) -> list:
    """
    检查已逾期的租借记录，并自动标记为逾期状态。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute(
        """SELECT id, item_id FROM records
           WHERE status = '借出中' AND expected_return_date < ?""",
        (today,),
    ).fetchall()

    for row in rows:
        conn.execute("UPDATE records SET status = '逾期', updated_at = datetime('now','localtime') WHERE id = ?",
                     (row["id"],))
        update_item_status(conn, row["item_id"])

    if rows:
        conn.commit()

    return [r["id"] for r in rows]


async def send_approval_reminder(phone: str, record_info: dict) -> bool:
    """发送审核提醒短信"""
    adapter = _get_sms_adapter()
    return await adapter.send_notification(
        phone,
        settings.SMS_TEMPLATE_CODE,
        {
            "borrower": record_info.get("borrower_name", ""),
            "item": record_info.get("item_name", ""),
        },
    )


async def send_return_reminder(phone: str, record_info: dict) -> bool:
    """发送归还提醒短信"""
    adapter = _get_sms_adapter()
    return await adapter.send_notification(
        phone,
        settings.SMS_TEMPLATE_CODE,
        {
            "borrower": record_info.get("borrower_name", ""),
            "item": record_info.get("item_name", ""),
        },
    )
