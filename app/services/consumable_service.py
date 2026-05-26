"""消耗品领用服务"""
from sqlalchemy import text
from app.utils.helpers import generate_consumable_doc_no


def submit_consumable(conn, data: dict, created_by: int, user_id: int) -> dict:
    """提交消耗品领用申请"""
    # 检查库存
    stock = conn.execute(text(
        "SELECT quantity FROM warehouse_stocks WHERE item_id = :iid AND warehouse_id = :wid"
    ), {"iid": data["item_id"], "wid": data["source_warehouse_id"]}).fetchone()
    available = stock["quantity"] if stock else 0

    # 减去待审核的领用数量
    pending_qty = conn.execute(text(
        "SELECT COALESCE(SUM(quantity), 0) FROM consumable_records "
        "WHERE item_id = :iid AND source_warehouse_id = :wid AND status = '待审核'"
    ), {"iid": data["item_id"], "wid": data["source_warehouse_id"]}).fetchone()[0]
    available -= pending_qty

    if available < data["quantity"]:
        raise ValueError(f"库存不足（可用：{available}，申请：{data['quantity']}）")

    doc_no = generate_consumable_doc_no(conn)
    conn.execute(text(
        "INSERT INTO consumable_records (document_no, item_id, user_id, quantity, "
        "pickup_date, reason, status, source_warehouse_id, created_by) "
        "VALUES (:dn, :iid, :uid, :qty, :pd, :rs, '待审核', :swid, :cb)"
    ), {
        "dn": doc_no, "iid": data["item_id"], "uid": user_id,
        "qty": data["quantity"], "pd": data["pickup_date"],
        "rs": data.get("reason", ""), "swid": data["source_warehouse_id"],
        "cb": created_by,
    })
    return {"document_no": doc_no}


def submit_batch_consumable(conn, data: dict, created_by: int, user_id: int) -> dict:
    """批量提交消耗品领用申请（同一单据号）"""
    doc_no = generate_consumable_doc_no(conn)

    for item in data["items"]:
        stock = conn.execute(text(
            "SELECT quantity FROM warehouse_stocks WHERE item_id = :iid AND warehouse_id = :wid"
        ), {"iid": item["item_id"], "wid": item["source_warehouse_id"]}).fetchone()
        available = stock["quantity"] if stock else 0

        pending_qty = conn.execute(text(
            "SELECT COALESCE(SUM(quantity), 0) FROM consumable_records "
            "WHERE item_id = :iid AND source_warehouse_id = :wid AND status = '待审核'"
        ), {"iid": item["item_id"], "wid": item["source_warehouse_id"]}).fetchone()[0]
        available -= pending_qty

        if available < item["quantity"]:
            raise ValueError(f"物品 ID:{item['item_id']} 库存不足（可用：{available}，申请：{item['quantity']}）")

        conn.execute(text(
            "INSERT INTO consumable_records (document_no, item_id, user_id, quantity, "
            "pickup_date, reason, status, source_warehouse_id, created_by) "
            "VALUES (:dn, :iid, :uid, :qty, :pd, :rs, '待审核', :swid, :cb)"
        ), {
            "dn": doc_no, "iid": item["item_id"], "uid": user_id,
            "qty": item["quantity"], "pd": data["pickup_date"],
            "rs": data.get("reason", ""), "swid": item["source_warehouse_id"],
            "cb": created_by,
        })

    return {"document_no": doc_no}


def approve_consumable(conn, record_id: int, approved_by: int):
    """审核通过消耗品领用 — 永久扣减库存"""
    record = conn.execute(text(
        "SELECT * FROM consumable_records WHERE id = :rid"
    ), {"rid": record_id}).fetchone()
    if not record:
        raise ValueError("领用记录不存在")
    if record["status"] != "待审核":
        raise ValueError("只能审核待审核状态的领用记录")

    # 扣减仓库库存
    conn.execute(text(
        "UPDATE warehouse_stocks SET quantity = quantity - :qty "
        "WHERE item_id = :iid AND warehouse_id = :wid"
    ), {"qty": record["quantity"], "iid": record["item_id"], "wid": record["source_warehouse_id"]})

    # 更新物品总库存
    conn.execute(text(
        "UPDATE items SET total_quantity = total_quantity - :qty, updated_at = NOW() WHERE id = :iid"
    ), {"qty": record["quantity"], "iid": record["item_id"]})

    # 更新领用记录状态
    conn.execute(text(
        "UPDATE consumable_records SET status = '已领取', approved_by = :ab, "
        "updated_at = NOW() WHERE id = :rid"
    ), {"ab": approved_by, "rid": record_id})


def reject_consumable(conn, record_id: int):
    """驳回消耗品领用"""
    record = conn.execute(text(
        "SELECT * FROM consumable_records WHERE id = :rid"
    ), {"rid": record_id}).fetchone()
    if not record:
        raise ValueError("领用记录不存在")
    if record["status"] != "待审核":
        raise ValueError("只能驳回待审核状态的领用记录")

    conn.execute(text(
        "UPDATE consumable_records SET status = '已拒绝', updated_at = NOW() WHERE id = :rid"
    ), {"rid": record_id})
