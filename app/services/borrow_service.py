"""租借引擎：申请提交、库存检查、状态流转"""
import sqlite3
from app.state_machine.transitions import can_transition
from app.state_machine.events import SUBMIT_BORROW, RESUBMIT
from app.services.inventory_service import reserve_stock, update_item_status, check_stock
from app.services.audit_service import log
from app.config import settings
from app.utils.helpers import deadline_str, generate_document_no


def submit_borrow(
    conn: sqlite3.Connection,
    item_id: int,
    borrower_id: int,
    borrower_name: str,
    quantity: int,
    borrow_date: str,
    expected_return_date: str,
    reason: str = "",
    contact: str = "",
) -> dict:
    """
    提交租借申请。
    1. 校验库存
    2. 在事务中预留库存并创建记录
    3. 设置审核截止时间
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        # 库存检查 + 预留
        if not reserve_stock(conn, item_id, quantity):
            conn.rollback()
            raise ValueError("库存不足，无法提交申请")

        # 创建租借记录
        deadline = deadline_str(settings.APPROVAL_TIMEOUT_HOURS)
        document_no = generate_document_no(conn)
        cursor = conn.execute(
            """INSERT INTO records
               (item_id, borrower_id, borrower_name, contact, quantity, borrow_date,
                expected_return_date, reason, status, approval_deadline, created_by, document_no)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, '待审核', ?, ?, ?)""",
            (item_id, borrower_id, borrower_name, contact, quantity,
             borrow_date, expected_return_date, reason, deadline, borrower_id, document_no),
        )
        record_id = cursor.lastrowid

        # 更新物品状态
        update_item_status(conn, item_id)

        # 操作日志
        log(conn, borrower_id, borrower_name, "borrow", "record", record_id,
            f"提交租借申请：物品ID={item_id}，数量={quantity}，预计归还={expected_return_date}")

        conn.commit()
        return {"record_id": record_id, "document_no": document_no, "message": "租借申请已提交，等待审核"}
    except Exception:
        conn.rollback()
        raise


def resubmit_borrow(
    conn: sqlite3.Connection,
    record_id: int,
    borrower_id: int,
    borrower_name: str,
    quantity: int,
    borrow_date: str,
    expected_return_date: str,
    reason: str = "",
    contact: str = "",
) -> dict:
    """
    驳回后重新提交申请。
    1. 校验原记录状态为"已拒绝"
    2. 检查库存
    3. 更新记录状态回"待审核"
    """
    record = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
    if not record:
        raise ValueError("租借记录不存在")
    if record["status"] != "已拒绝":
        raise ValueError(f"当前状态 [{record['status']}] 不允许重新提交")
    if record["borrower_id"] != borrower_id:
        raise ValueError("只能重新提交自己的申请")

    if not can_transition(record["status"], RESUBMIT):
        raise ValueError(f"不允许从 [{record['status']}] 重新提交")

    conn.execute("BEGIN IMMEDIATE")
    try:
        # 重新检查库存
        if not reserve_stock(conn, record["item_id"], quantity):
            conn.rollback()
            raise ValueError("库存不足，无法重新提交")

        deadline = deadline_str(settings.APPROVAL_TIMEOUT_HOURS)
        conn.execute(
            """UPDATE records SET quantity = ?, borrow_date = ?, expected_return_date = ?,
               reason = ?, contact = ?, status = '待审核', approval_deadline = ?,
               updated_at = datetime('now','localtime') WHERE id = ?""",
            (quantity, borrow_date, expected_return_date, reason, contact, deadline, record_id),
        )

        update_item_status(conn, record["item_id"])
        log(conn, borrower_id, borrower_name, "resubmit", "record", record_id,
            f"重新提交租借申请：数量={quantity}，预计归还={expected_return_date}")
        conn.commit()
        return {"message": "申请已重新提交，等待审核"}
    except Exception:
        conn.rollback()
        raise


def submit_batch_borrow(
    conn: sqlite3.Connection,
    items: list[dict],
    borrower_id: int,
    borrower_name: str,
    borrow_date: str,
    expected_return_date: str,
    reason: str = "",
    contact: str = "",
) -> dict:
    """
    批量提交租借申请（购物车模式）。
    在单个事务中处理所有物品，任一库存不足则全部回滚。
    """
    if not items:
        raise ValueError("租借物品列表不能为空")

    conn.execute("BEGIN IMMEDIATE")
    try:
        # Phase 1: 校验所有物品库存充足
        for item in items:
            if not check_stock(conn, item["item_id"], item["quantity"]):
                conn.rollback()
                raise ValueError(f"物品ID={item['item_id']} 库存不足，无法提交申请")

        # Phase 2: 生成单一单据号并创建记录
        deadline = deadline_str(settings.APPROVAL_TIMEOUT_HOURS)
        document_no = generate_document_no(conn)
        record_ids = []

        for item in items:
            cursor = conn.execute(
                """INSERT INTO records
                   (item_id, borrower_id, borrower_name, contact, quantity, borrow_date,
                    expected_return_date, reason, status, approval_deadline, created_by, document_no)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, '待审核', ?, ?, ?)""",
                (item["item_id"], borrower_id, borrower_name, contact,
                 item["quantity"], borrow_date, expected_return_date,
                 reason, deadline, borrower_id, document_no),
            )
            record_ids.append(cursor.lastrowid)

            update_item_status(conn, item["item_id"])

            log(conn, borrower_id, borrower_name, "batch_borrow", "record",
                cursor.lastrowid,
                f"批量租借申请：物品ID={item['item_id']}，数量={item['quantity']}，"
                f"预计归还={expected_return_date}")

        conn.commit()
        return {
            "record_ids": record_ids,
            "document_no": document_no,
            "count": len(record_ids),
            "message": f"批量租借申请已提交（单据号: {document_no}），共 {len(record_ids)} 件物品，等待审核",
        }
    except Exception:
        conn.rollback()
        raise
