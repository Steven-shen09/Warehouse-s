"""采购入库服务"""
from sqlalchemy import text
from app.utils.helpers import generate_purchase_doc_no
from app.services.asset_code_service import generate_asset_code


def create_purchase_order(conn, data: dict, created_by: int) -> dict:
    """创建采购入库单"""
    doc_no = generate_purchase_doc_no(conn)
    total_amount = sum(
        item["quantity"] * item["unit_price"]
        for item in data["items"]
    )

    result = conn.execute(text(
        "INSERT INTO purchase_orders (document_no, supplier_id, warehouse_id, status, "
        "total_amount, purchase_date, notes, created_by) "
        "VALUES (:dn, :sid, :wid, '待审核', :ta, :pd, :nt, :cb) RETURNING id"
    ), {
        "dn": doc_no, "sid": data["supplier_id"], "wid": data["warehouse_id"],
        "ta": total_amount, "pd": data["purchase_date"], "nt": data.get("notes", ""),
        "cb": created_by,
    })
    po_id = result.fetchone()[0]

    for item in data["items"]:
        conn.execute(text(
            "INSERT INTO purchase_order_items (purchase_order_id, item_id, quantity, "
            "unit_price, batch_no, production_date, expiry_date, notes) "
            "VALUES (:pid, :iid, :qty, :up, :bn, :prd, :exd, :nt)"
        ), {
            "pid": po_id, "iid": item["item_id"], "qty": item["quantity"],
            "up": item["unit_price"], "bn": item.get("batch_no", ""),
            "prd": item.get("production_date"), "exd": item.get("expiry_date"),
            "nt": item.get("notes", ""),
        })

    return {"id": po_id, "document_no": doc_no}


def approve_purchase_order(conn, purchase_order_id: int, approved_by: int):
    """审核通过采购入库单，执行入库操作"""
    po = conn.execute(text(
        "SELECT * FROM purchase_orders WHERE id = :pid"
    ), {"pid": purchase_order_id}).fetchone()
    if not po:
        raise ValueError("采购单不存在")
    if po["status"] != "待审核":
        raise ValueError("只能审核待审核状态的采购单")

    items = conn.execute(text(
        "SELECT poi.*, i.item_type, i.name, i.abbreviation "
        "FROM purchase_order_items poi JOIN items i ON poi.item_id = i.id "
        "WHERE poi.purchase_order_id = :pid"
    ), {"pid": purchase_order_id}).fetchall()

    for poi in items:
        item_dict = {
            "id": poi["item_id"], "name": poi["name"],
            "abbreviation": poi["abbreviation"], "item_type": poi["item_type"],
        }
        purchase_date_str = po["purchase_date"]
        if hasattr(purchase_date_str, "strftime"):
            purchase_date_str = purchase_date_str.strftime("%Y%m%d")

        # 1. 更新仓库库存
        existing = conn.execute(text(
            "SELECT id, quantity FROM warehouse_stocks WHERE item_id = :iid AND warehouse_id = :wid"
        ), {"iid": poi["item_id"], "wid": po["warehouse_id"]}).fetchone()
        if existing:
            conn.execute(text(
                "UPDATE warehouse_stocks SET quantity = quantity + :qty WHERE id = :sid"
            ), {"qty": poi["quantity"], "sid": existing["id"]})
        else:
            conn.execute(text(
                "INSERT INTO warehouse_stocks (item_id, warehouse_id, quantity) VALUES (:iid, :wid, :qty)"
            ), {"iid": poi["item_id"], "wid": po["warehouse_id"], "qty": poi["quantity"]})

        # 2. 更新 items.total_quantity
        conn.execute(text(
            "UPDATE items SET total_quantity = total_quantity + :qty, updated_at = NOW() WHERE id = :iid"
        ), {"qty": poi["quantity"], "iid": poi["item_id"]})

        # 3. 如果是固定资产，生成资产实例
        if poi["item_type"] == "fixed_asset":
            for i in range(poi["quantity"]):
                asset_code = generate_asset_code(
                    conn, item_dict, purchase_date_str,
                    poi["batch_no"] or "", i + 1
                )
                conn.execute(text(
                    "INSERT INTO asset_instances (item_id, asset_code, status, "
                    "purchase_date, purchase_order_item_id, warehouse_id) "
                    "VALUES (:iid, :ac, '在库', :pd, :poiid, :wid)"
                ), {
                    "iid": poi["item_id"], "ac": asset_code,
                    "pd": po["purchase_date"], "poiid": poi["id"],
                    "wid": po["warehouse_id"],
                })

    # 4. 更新采购单状态
    conn.execute(text(
        "UPDATE purchase_orders SET status = '已入库', approved_by = :ab, updated_at = NOW() WHERE id = :pid"
    ), {"ab": approved_by, "pid": purchase_order_id})


def cancel_purchase_order(conn, purchase_order_id: int):
    """取消采购单"""
    po = conn.execute(text(
        "SELECT * FROM purchase_orders WHERE id = :pid"
    ), {"pid": purchase_order_id}).fetchone()
    if not po:
        raise ValueError("采购单不存在")
    if po["status"] != "待审核":
        raise ValueError("只能取消待审核状态的采购单")

    conn.execute(text(
        "UPDATE purchase_orders SET status = '已取消', updated_at = NOW() WHERE id = :pid"
    ), {"pid": purchase_order_id})
