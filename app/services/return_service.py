"""归还引擎：部分归还、库存释放"""
import sqlite3
from app.state_machine.transitions import can_transition
from app.state_machine.events import RETURN_FULL, RETURN_PARTIAL
from app.services.inventory_service import update_item_status
from app.services.audit_service import log


def process_return(
    conn: sqlite3.Connection,
    record_id: int,
    return_quantity: int,
    operator_id: int,
    operator_name: str,
    actual_return_date: str = "",
    return_notes: str = "",
) -> dict:
    """
    处理归还（支持部分归还）。
    1. 校验归还数量不超过借出数量
    2. 完全归还：记录状态 → 已归还，填写实际归还日期
    3. 部分归还：原记录数量扣减，创建剩余记录
    """
    record = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
    if not record:
        raise ValueError("租借记录不存在")

    # 计算该记录对应的未归还数量
    remaining = _get_remaining_quantity(conn, record)

    if return_quantity <= 0:
        raise ValueError("归还数量必须大于 0")
    if return_quantity > remaining:
        raise ValueError(f"归还数量 ({return_quantity}) 超过未归还数量 ({remaining})")

    item_id = record["item_id"]
    is_full_return = return_quantity == remaining

    if is_full_return:
        # 完全归还
        event = RETURN_FULL
        if not can_transition(record["status"], event):
            raise ValueError(f"当前状态 [{record['status']}] 不允许归还操作")

        conn.execute(
            """UPDATE records SET status = '已归还', actual_return_date = ?,
               return_notes = ?, updated_at = datetime('now','localtime') WHERE id = ?""",
            (actual_return_date, return_notes, record_id),
        )
    else:
        # 部分归还：创建新的"已归还"记录来记录归还数量，原记录数量扣减
        event = RETURN_PARTIAL
        if not can_transition(record["status"], event):
            raise ValueError(f"当前状态 [{record['status']}] 不允许部分归还")

        # 将原记录数量扣减
        new_remaining = remaining - return_quantity
        conn.execute(
            "UPDATE records SET quantity = ?, updated_at = datetime('now','localtime') WHERE id = ?",
            (new_remaining, record_id),
        )

        # 通过 return_notes 记录本次归还信息
        conn.execute(
            """UPDATE records SET return_notes = ? WHERE id = ?""",
            (f"[部分归还] 归还{return_quantity}件，备注：{return_notes}" if return_notes else f"[部分归还] 归还{return_quantity}件",
             record_id),
        )

    # 更新物品状态
    update_item_status(conn, item_id)

    # 操作日志
    log(conn, operator_id, operator_name,
        "return_full" if is_full_return else "return_partial",
        "record", record_id,
        f"{'完全' if is_full_return else '部分'}归还：数量={return_quantity}")

    conn.commit()
    return {
        "message": f"{'完全' if is_full_return else '部分'}归还成功",
        "is_full_return": is_full_return,
        "return_quantity": return_quantity,
    }


def _get_remaining_quantity(conn: sqlite3.Connection, record: dict) -> int:
    """计算某记录的当前未归还数量"""
    # 如果有 original_record_id，表示这是被拆分的记录的一部分
    # 直接返回当前记录 quantity 即可
    return record["quantity"]


def process_return_by_document(
    conn: sqlite3.Connection,
    document_no: str,
    operator_id: int,
    operator_name: str,
    actual_return_date: str = "",
    return_notes: str = "",
) -> dict:
    """按单据号批量归还"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        records = conn.execute(
            "SELECT * FROM records WHERE document_no = ? AND status IN ('借出中', '逾期')",
            (document_no,)
        ).fetchall()
        if not records:
            conn.rollback()
            raise ValueError(f"单据 {document_no} 下没有可归还的记录")

        returned_count = 0
        for record in records:
            if not can_transition(record["status"], RETURN_FULL):
                continue
            conn.execute(
                """UPDATE records SET status = '已归还', actual_return_date = ?,
                   return_notes = ?, updated_at = datetime('now','localtime') WHERE id = ?""",
                (actual_return_date, return_notes, record["id"])
            )
            update_item_status(conn, record["item_id"])
            log(conn, operator_id, operator_name, "return_full", "record", record["id"],
                f"批量归还（单据号: {document_no}）")
            returned_count += 1

        conn.commit()
        return {
            "message": f"单据 {document_no} 下 {returned_count} 条记录已归还",
            "returned_count": returned_count,
            "document_no": document_no,
        }
    except Exception:
        conn.rollback()
        raise
