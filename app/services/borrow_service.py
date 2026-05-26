"""租借引擎：申请提交、库存检查、状态流转"""
from sqlalchemy import text
from app.state_machine.transitions import can_transition
from app.state_machine.events import SUBMIT_BORROW, RESUBMIT
from app.services.inventory_service import reserve_stock, update_item_status, check_stock
from app.services.audit_service import log
from app.config import settings
from app.utils.helpers import deadline_str, generate_document_no


def submit_borrow(conn, item_id, borrower_id, borrower_name, quantity, borrow_date, expected_return_date, reason="", contact="", source_warehouse_id=None):
    conn.rollback()
    with conn.begin():
        if not reserve_stock(conn, item_id, quantity):
            raise ValueError("库存不足，无法提交申请")

        # 未指定来源仓库时，自动选库存 >= 借出数量的仓库（优先库存最多的）
        if source_warehouse_id is None:
            wh_row = conn.execute(text(
                "SELECT warehouse_id FROM warehouse_stocks WHERE item_id = :iid AND quantity >= :qty ORDER BY quantity DESC LIMIT 1"
            ), {"iid": item_id, "qty": quantity}).fetchone()
            if wh_row:
                source_warehouse_id = wh_row[0]
            else:
                # 没有单个仓库够，尝试找库存最多的那个
                wh_row = conn.execute(text(
                    "SELECT warehouse_id, quantity FROM warehouse_stocks WHERE item_id = :iid AND quantity > 0 ORDER BY quantity DESC LIMIT 1"
                ), {"iid": item_id}).fetchone()
                if wh_row:
                    raise ValueError(
                        f"该物品最大单仓库存为 {wh_row[1]} 件，不足以借出 {quantity} 件。"
                        f"请分多次从不同仓库借出，或在调拨中先将库存集中。"
                    )
                else:
                    raise ValueError("该物品无可用仓库")

        deadline = deadline_str(settings.APPROVAL_TIMEOUT_HOURS)
        document_no = generate_document_no(conn)
        result = conn.execute(text(
            """INSERT INTO records
               (item_id, borrower_id, borrower_name, contact, quantity, borrow_date,
                expected_return_date, reason, status, approval_deadline, created_by, document_no, source_warehouse_id)
               VALUES (:iid, :bid, :bname, :contact, :qty, :bdate, :rdate, :reason, '待审核', :deadline, :cby, :dno, :swid)
               RETURNING id"""
        ), {"iid": item_id, "bid": borrower_id, "bname": borrower_name, "contact": contact,
            "qty": quantity, "bdate": borrow_date, "rdate": expected_return_date,
            "reason": reason, "deadline": deadline, "cby": borrower_id, "dno": document_no, "swid": source_warehouse_id})
        record_id = result.fetchone()[0]

        update_item_status(conn, item_id)
        log(conn, borrower_id, borrower_name, "borrow", "record", record_id,
            f"提交租借申请：物品ID={item_id}，数量={quantity}，预计归还={expected_return_date}")

        return {"record_id": record_id, "document_no": document_no, "message": "租借申请已提交，等待审核"}


def resubmit_borrow(
    conn,
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
    record = conn.execute(text("SELECT * FROM records WHERE id = :rid"), {"rid": record_id}).fetchone()
    if not record:
        raise ValueError("租借记录不存在")
    if record["status"] != "已拒绝":
        raise ValueError(f"当前状态 [{record['status']}] 不允许重新提交")
    if record["borrower_id"] != borrower_id:
        raise ValueError("只能重新提交自己的申请")

    if not can_transition(record["status"], RESUBMIT):
        raise ValueError(f"不允许从 [{record['status']}] 重新提交")

    conn.rollback()
    with conn.begin():
        # 重新检查库存
        if not reserve_stock(conn, record["item_id"], quantity):
            raise ValueError("库存不足，无法重新提交")

        deadline = deadline_str(settings.APPROVAL_TIMEOUT_HOURS)
        conn.execute(text(
            """UPDATE records SET quantity = :qty, borrow_date = :bdate, expected_return_date = :rdate,
               reason = :reason, contact = :contact, status = '待审核', approval_deadline = :deadline,
               updated_at = NOW() WHERE id = :rid"""
        ), {"qty": quantity, "bdate": borrow_date, "rdate": expected_return_date,
            "reason": reason, "contact": contact, "deadline": deadline, "rid": record_id})

        update_item_status(conn, record["item_id"])
        log(conn, borrower_id, borrower_name, "resubmit", "record", record_id,
            f"重新提交租借申请：数量={quantity}，预计归还={expected_return_date}")
        return {"message": "申请已重新提交，等待审核"}


def submit_batch_borrow(
    conn,
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

    conn.rollback()
    with conn.begin():
        # Phase 1: 校验所有物品库存充足
        for item in items:
            if not check_stock(conn, item["item_id"], item["quantity"]):
                raise ValueError(f"物品ID={item['item_id']} 库存不足，无法提交申请")

        # Phase 2: 生成单一单据号并创建记录
        deadline = deadline_str(settings.APPROVAL_TIMEOUT_HOURS)
        document_no = generate_document_no(conn)
        record_ids = []

        for item in items:
            swid = item.get("warehouse_id")
            if swid is not None:
                # 指定了仓库：整单从该仓库出
                result = conn.execute(text(
                    """INSERT INTO records
                       (item_id, borrower_id, borrower_name, contact, quantity, borrow_date,
                        expected_return_date, reason, status, approval_deadline, created_by, document_no, source_warehouse_id)
                       VALUES (:iid, :bid, :bname, :contact, :qty, :bdate, :rdate,
                               :reason, '待审核', :deadline, :cby, :dno, :swid)
                       RETURNING id"""),
                    {"iid": item["item_id"], "bid": borrower_id, "bname": borrower_name,
                     "contact": contact, "qty": item["quantity"], "bdate": borrow_date,
                     "rdate": expected_return_date, "reason": reason, "deadline": deadline,
                     "cby": borrower_id, "dno": document_no, "swid": swid})
                record_id = result.fetchone()[0]
                record_ids.append(record_id)
                update_item_status(conn, item["item_id"])
                log(conn, borrower_id, borrower_name, "batch_borrow", "record",
                    record_id,
                    f"批量租借申请：物品ID={item['item_id']}，数量={item['quantity']}，"
                    f"预计归还={expected_return_date}")
            else:
                # 未指定仓库：按各仓库库存比例分流
                wh_stocks = conn.execute(text(
                    "SELECT warehouse_id, quantity FROM warehouse_stocks WHERE item_id = :iid AND quantity > 0 ORDER BY quantity DESC"
                ), {"iid": item["item_id"]}).fetchall()
                remaining = item["quantity"]
                total_stock = sum(s[1] for s in wh_stocks)
                for s in wh_stocks:
                    wh_id, wh_qty = s[0], s[1]
                    if remaining <= 0:
                        break
                    alloc = max(1, round(item["quantity"] * wh_qty / total_stock))
                    alloc = min(alloc, remaining, wh_qty)
                    result = conn.execute(text(
                        """INSERT INTO records
                           (item_id, borrower_id, borrower_name, contact, quantity, borrow_date,
                            expected_return_date, reason, status, approval_deadline, created_by, document_no, source_warehouse_id)
                           VALUES (:iid, :bid, :bname, :contact, :qty, :bdate, :rdate,
                                   :reason, '待审核', :deadline, :cby, :dno, :swid)
                           RETURNING id"""),
                        {"iid": item["item_id"], "bid": borrower_id, "bname": borrower_name,
                         "contact": contact, "qty": alloc, "bdate": borrow_date,
                         "rdate": expected_return_date, "reason": reason, "deadline": deadline,
                         "cby": borrower_id, "dno": document_no, "swid": wh_id})
                    record_id = result.fetchone()[0]
                    record_ids.append(record_id)
                    remaining -= alloc
                    update_item_status(conn, item["item_id"])
                    log(conn, borrower_id, borrower_name, "batch_borrow", "record",
                        record_id,
                        f"批量租借申请：物品ID={item['item_id']}，数量={alloc}(来自仓库{wh_id})，"
                        f"预计归还={expected_return_date}")

        return {
            "record_ids": record_ids,
            "document_no": document_no,
            "count": len(record_ids),
            "message": f"批量租借申请已提交（单据号: {document_no}），共 {len(record_ids)} 件物品，等待审核",
        }
