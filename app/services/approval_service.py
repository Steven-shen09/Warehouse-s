"""审核工作流：审批通过/驳回、超时检测"""
import sqlite3
from app.state_machine.transitions import can_transition
from app.state_machine.events import APPROVE, REJECT
from app.services.audit_service import log
from app.services.inventory_service import update_item_status
from app.utils.helpers import now_str


def approve(
    conn: sqlite3.Connection,
    record_id: int,
    approver_id: int,
    approver_name: str,
    comment: str = "",
    ai_suggestion: str = "",
) -> dict:
    """
    审核通过。
    1. 校验记录状态为"待审核"
    2. 更新状态为"借出中"
    3. 记录审核日志
    """
    record = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
    if not record:
        raise ValueError("租借记录不存在")

    if not can_transition(record["status"], APPROVE):
        raise ValueError(f"当前状态 [{record['status']}] 不允许审核通过")

    conn.execute(
        """UPDATE records SET status = '借出中', updated_at = datetime('now','localtime')
           WHERE id = ?""",
        (record_id,),
    )

    update_item_status(conn, record["item_id"])

    # 记录审核
    conn.execute(
        """INSERT INTO approvals (record_id, approver_id, action, comment, ai_suggestion)
           VALUES (?, ?, 'approved', ?, ?)""",
        (record_id, approver_id, comment, ai_suggestion),
    )

    # 操作日志
    log(conn, approver_id, approver_name, "approve", "record", record_id,
        f"审核通过：{comment}" if comment else "审核通过")

    conn.commit()
    return {"message": "审核已通过，物品已借出"}


def reject(
    conn: sqlite3.Connection,
    record_id: int,
    approver_id: int,
    approver_name: str,
    comment: str,
) -> dict:
    """
    审核驳回（须填写原因）。
    1. 校验记录状态为"待审核"
    2. 更新状态为"已拒绝"
    3. 记录驳回原因
    """
    if not comment or not comment.strip():
        raise ValueError("驳回必须填写原因")

    record = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
    if not record:
        raise ValueError("租借记录不存在")

    if not can_transition(record["status"], REJECT):
        raise ValueError(f"当前状态 [{record['status']}] 不允许驳回")

    conn.execute(
        "UPDATE records SET status = '已拒绝', updated_at = datetime('now','localtime') WHERE id = ?",
        (record_id,),
    )

    update_item_status(conn, record["item_id"])

    # 记录审核
    conn.execute(
        """INSERT INTO approvals (record_id, approver_id, action, comment)
           VALUES (?, ?, 'rejected', ?)""",
        (record_id, approver_id, comment),
    )

    # 操作日志
    log(conn, approver_id, approver_name, "reject", "record", record_id,
        f"审核驳回：{comment}")

    conn.commit()
    return {"message": "申请已驳回"}


def get_pending_approvals(
    conn: sqlite3.Connection,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """获取待审核记录列表（含超时标记）"""
    now = now_str()
    # 同时更新已超时的记录状态
    conn.execute(
        """UPDATE records SET status = '逾期'
           WHERE status = '待审核' AND approval_deadline < ?""",
        (now,),
    )

    total = conn.execute("SELECT COUNT(*) FROM records WHERE status = '待审核'").fetchone()[0]
    offset = (page - 1) * page_size
    rows = conn.execute(
        """SELECT r.*, i.name as item_name
           FROM records r JOIN items i ON r.item_id = i.id
           WHERE r.status = '待审核'
           ORDER BY r.created_at ASC LIMIT ? OFFSET ?""",
        (page_size, offset),
    ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        item["is_overtime"] = row["approval_deadline"] and row["approval_deadline"] < now
        items.append(item)

    conn.commit()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_overdue_approvals_count(conn: sqlite3.Connection) -> int:
    """获取已超时的待审核记录数"""
    return conn.execute(
        "SELECT COUNT(*) FROM records WHERE status = '待审核' AND approval_deadline < datetime('now','localtime')"
    ).fetchone()[0]


def approve_by_document(
    conn: sqlite3.Connection,
    document_no: str,
    approver_id: int,
    approver_name: str,
    comment: str = "",
) -> dict:
    """按单据号批量审核通过"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        records = conn.execute(
            "SELECT * FROM records WHERE document_no = ? AND status = '待审核'",
            (document_no,)
        ).fetchall()
        if not records:
            conn.rollback()
            raise ValueError(f"单据 {document_no} 下没有待审核的记录")

        approved_count = 0
        for record in records:
            if not can_transition(record["status"], APPROVE):
                continue
            conn.execute(
                "UPDATE records SET status = '借出中', updated_at = datetime('now','localtime') WHERE id = ?",
                (record["id"],)
            )
            update_item_status(conn, record["item_id"])
            conn.execute(
                "INSERT INTO approvals (record_id, approver_id, action, comment) VALUES (?, ?, 'approved', ?)",
                (record["id"], approver_id, comment)
            )
            log(conn, approver_id, approver_name, "approve", "record", record["id"],
                f"批量审核通过（单据号: {document_no}）" + (f"：{comment}" if comment else ""))
            approved_count += 1

        conn.commit()
        return {
            "message": f"单据 {document_no} 下 {approved_count} 条记录已通过",
            "approved_count": approved_count,
            "document_no": document_no,
        }
    except Exception:
        conn.rollback()
        raise


def reject_by_document(
    conn: sqlite3.Connection,
    document_no: str,
    approver_id: int,
    approver_name: str,
    comment: str,
) -> dict:
    """按单据号批量驳回"""
    if not comment or not comment.strip():
        raise ValueError("驳回必须填写原因")

    conn.execute("BEGIN IMMEDIATE")
    try:
        records = conn.execute(
            "SELECT * FROM records WHERE document_no = ? AND status = '待审核'",
            (document_no,)
        ).fetchall()
        if not records:
            conn.rollback()
            raise ValueError(f"单据 {document_no} 下没有待审核的记录")

        rejected_count = 0
        for record in records:
            if not can_transition(record["status"], REJECT):
                continue
            conn.execute(
                "UPDATE records SET status = '已拒绝', updated_at = datetime('now','localtime') WHERE id = ?",
                (record["id"],)
            )
            update_item_status(conn, record["item_id"])
            conn.execute(
                "INSERT INTO approvals (record_id, approver_id, action, comment) VALUES (?, ?, 'rejected', ?)",
                (record["id"], approver_id, comment)
            )
            log(conn, approver_id, approver_name, "reject", "record", record["id"],
                f"批量驳回（单据号: {document_no}）：{comment}")
            rejected_count += 1

        conn.commit()
        return {
            "message": f"单据 {document_no} 下 {rejected_count} 条记录已驳回",
            "rejected_count": rejected_count,
            "document_no": document_no,
        }
    except Exception:
        conn.rollback()
        raise


def get_pending_approvals_grouped(
    conn: sqlite3.Connection,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """按单据号分组获取待审核记录"""
    now = now_str()
    conn.execute(
        "UPDATE records SET status = '逾期' WHERE status = '待审核' AND approval_deadline < ?",
        (now,),
    )

    # 统计单据分组数（NULL 的单条记录各自成组）
    total = conn.execute(
        "SELECT COUNT(DISTINCT COALESCE(document_no, 'SINGLE_' || id)) FROM records WHERE status = '待审核'"
    ).fetchone()[0]

    offset = (page - 1) * page_size
    doc_rows = conn.execute(
        """SELECT COALESCE(document_no, 'SINGLE_' || id) as doc_key,
                  document_no, borrower_name, borrow_date, expected_return_date,
                  reason, contact, MIN(approval_deadline) as earliest_deadline,
                  COUNT(*) as item_count,
                  GROUP_CONCAT(r.id) as record_ids
           FROM records r
           WHERE r.status = '待审核'
           GROUP BY doc_key
           ORDER BY MIN(r.created_at) ASC LIMIT ? OFFSET ?""",
        (page_size, offset),
    ).fetchall()

    documents = []
    for doc_row in doc_rows:
        record_ids = [int(x) for x in doc_row["record_ids"].split(",")]
        placeholders = ",".join("?" * len(record_ids))
        rows = conn.execute(
            f"""SELECT r.*, i.name as item_name
                FROM records r JOIN items i ON r.item_id = i.id
                WHERE r.id IN ({placeholders})""",
            record_ids,
        ).fetchall()
        items_list = []
        for row in rows:
            item = dict(row)
            item["is_overtime"] = bool(row["approval_deadline"] and row["approval_deadline"] < now)
            items_list.append(item)

        documents.append({
            "document_no": doc_row["document_no"],
            "borrower_name": doc_row["borrower_name"],
            "borrow_date": doc_row["borrow_date"],
            "expected_return_date": doc_row["expected_return_date"],
            "reason": doc_row["reason"],
            "contact": doc_row["contact"],
            "earliest_deadline": doc_row["earliest_deadline"],
            "item_count": doc_row["item_count"],
            "is_overtime": bool(doc_row["earliest_deadline"] and doc_row["earliest_deadline"] < now),
            "items": items_list,
            "record_ids": record_ids,
        })

    conn.commit()
    return {"documents": documents, "total": total, "page": page, "page_size": page_size}
