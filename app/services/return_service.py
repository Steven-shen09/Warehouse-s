"""归还引擎：部分归还、库存释放"""
from sqlalchemy import text
from app.state_machine.transitions import can_transition
from app.state_machine.events import RETURN_FULL, RETURN_PARTIAL
from app.services.inventory_service import update_item_status
from app.services.audit_service import log


def process_return(
    conn,
    record_id: int,
    return_quantity: int,
    operator_id: int,
    operator_name: str,
    actual_return_date: str = "",
    return_notes: str = "",
) -> dict:
    record = conn.execute(text("SELECT * FROM records WHERE id = :rid"), {"rid": record_id}).fetchone()
    if not record:
        raise ValueError("租借记录不存在")
    remaining = _get_remaining_quantity(conn, record)
    if return_quantity <= 0:
        raise ValueError("归还数量必须大于 0")
    if return_quantity > remaining:
        raise ValueError(f"归还数量 ({return_quantity}) 超过未归还数量 ({remaining})")

    item_id = record["item_id"]
    is_full_return = return_quantity == remaining

    conn.rollback()
    with conn.begin():
        if is_full_return:
            event = RETURN_FULL
            if not can_transition(record["status"], event):
                raise ValueError(f"当前状态 [{record['status']}] 不允许归还操作")
            conn.execute(text(
                """UPDATE records SET status = '已归还', actual_return_date = :ardate,
                   return_notes = :notes, updated_at = NOW() WHERE id = :rid"""),
                {"ardate": actual_return_date, "notes": return_notes, "rid": record_id},
            )
        else:
            event = RETURN_PARTIAL
            if not can_transition(record["status"], event):
                raise ValueError(f"当前状态 [{record['status']}] 不允许部分归还")
            new_remaining = remaining - return_quantity
            conn.execute(text(
                "UPDATE records SET quantity = :qty, updated_at = NOW() WHERE id = :rid"),
                {"qty": new_remaining, "rid": record_id},
            )
            conn.execute(text(
                """UPDATE records SET return_notes = :notes WHERE id = :rid"""),
                {"notes": f"[部分归还] 归还{return_quantity}件，备注：{return_notes}" if return_notes else f"[部分归还] 归还{return_quantity}件",
                 "rid": record_id},
            )
        update_item_status(conn, item_id)
        log(conn, operator_id, operator_name,
            "return_full" if is_full_return else "return_partial",
            "record", record_id,
            f"{'完全' if is_full_return else '部分'}归还：数量={return_quantity}")

    return {
        "message": f"{'完全' if is_full_return else '部分'}归还成功",
        "is_full_return": is_full_return,
        "return_quantity": return_quantity,
    }


def _get_remaining_quantity(conn, record: dict) -> int:
    return record["quantity"]


def process_return_by_document(
    conn,
    document_no: str,
    operator_id: int,
    operator_name: str,
    actual_return_date: str = "",
    return_notes: str = "",
) -> dict:
    conn.rollback()
    with conn.begin():
        records = conn.execute(text(
            "SELECT * FROM records WHERE document_no = :dno AND status IN ('借出中', '逾期')"
        ), {"dno": document_no}).fetchall()
        if not records:
            raise ValueError(f"单据 {document_no} 下没有可归还的记录")

        returned_count = 0
        for record in records:
            if not can_transition(record["status"], RETURN_FULL):
                continue
            conn.execute(text(
                """UPDATE records SET status = '已归还', actual_return_date = :ardate,
                   return_notes = :notes, updated_at = NOW() WHERE id = :rid"""),
                {"ardate": actual_return_date, "notes": return_notes, "rid": record["id"]}
            )
            update_item_status(conn, record["item_id"])
            log(conn, operator_id, operator_name, "return_full", "record", record["id"],
                f"批量归还（单据号: {document_no}）")
            returned_count += 1

        return {
            "message": f"单据 {document_no} 下 {returned_count} 条记录已归还",
            "returned_count": returned_count,
            "document_no": document_no,
        }
