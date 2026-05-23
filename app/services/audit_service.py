"""审计服务：操作日志记录"""
import json
from sqlalchemy import text
from app.utils.helpers import now_str


def log(conn, user_id, username, action, target_type, target_id, detail="", ip_address=""):
    conn.execute(text(
        "INSERT INTO audit_logs (user_id, username, action, target_type, target_id, detail, ip_address) "
        "VALUES (:uid, :un, :act, :tt, :tid, :det, :ip)"
    ), {"uid": user_id, "un": username, "act": action, "tt": target_type, "tid": target_id, "det": detail, "ip": ip_address})


def get_logs(conn, page=1, page_size=50, action="", target_type="", username=""):
    from sqlalchemy import text
    where = "WHERE 1=1"
    params = {}
    if action:
        where += " AND action = :action"
        params["action"] = action
    if target_type:
        where += " AND target_type = :tt"
        params["tt"] = target_type
    if username:
        where += " AND username LIKE :uname"
        params["uname"] = f"%{username}%"

    total = conn.execute(text(f"SELECT COUNT(*) FROM audit_logs {where}"), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset
    rows = conn.execute(text(
        f"SELECT * FROM audit_logs {where} ORDER BY id DESC LIMIT :limit OFFSET :offset"
    ), params).fetchall()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
