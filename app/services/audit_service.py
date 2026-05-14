"""审计服务：操作日志记录"""
import sqlite3
import json
from app.utils.helpers import now_str


def log(
    conn: sqlite3.Connection,
    user_id: int,
    username: str,
    action: str,
    target_type: str,
    target_id: int,
    detail: str = "",
    ip_address: str = "",
):
    """
    记录操作日志。
    调用方须自行 commit。
    """
    conn.execute(
        """INSERT INTO audit_logs (user_id, username, action, target_type, target_id, detail, ip_address)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, username, action, target_type, target_id, detail, ip_address),
    )


def get_logs(
    conn: sqlite3.Connection,
    page: int = 1,
    page_size: int = 50,
    action: str = "",
    target_type: str = "",
    username: str = "",
) -> dict:
    """分页查询操作日志"""
    where = "WHERE 1=1"
    params = []
    if action:
        where += " AND action = ?"
        params.append(action)
    if target_type:
        where += " AND target_type = ?"
        params.append(target_type)
    if username:
        where += " AND username LIKE ?"
        params.append(f"%{username}%")

    total = conn.execute(f"SELECT COUNT(*) FROM audit_logs {where}", params).fetchone()[0]
    offset = (page - 1) * page_size
    rows = conn.execute(
        f"SELECT * FROM audit_logs {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [page_size, offset],
    ).fetchall()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
