"""库存服务：实时计算可用库存、事务保护"""
import sqlite3


def get_total_quantity(conn: sqlite3.Connection, item_id: int) -> int:
    """从 warehouse_stocks 汇总计算物品总库存"""
    total = conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) FROM warehouse_stocks WHERE item_id = ?", (item_id,)
    ).fetchone()[0]
    return total


def get_available_quantity(conn: sqlite3.Connection, item_id: int, warehouse_id: int = None) -> int:
    """计算物品的实时可用库存：总库存 - 已占用（借出中 + 逾期 + 待审核）"""
    item = conn.execute(
        "SELECT status FROM items WHERE id = ?", (item_id,)
    ).fetchone()
    if not item:
        return 0

    if item["status"] == "损坏":
        return 0

    if warehouse_id:
        total = conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM warehouse_stocks WHERE item_id = ? AND warehouse_id = ?",
            (item_id, warehouse_id),
        ).fetchone()[0]
    else:
        total = get_total_quantity(conn, item_id)

    reserved = conn.execute(
        """SELECT COALESCE(SUM(quantity), 0) FROM records
           WHERE item_id = ? AND status IN ('借出中', '逾期', '待审核')""",
        (item_id,),
    ).fetchone()[0]

    return max(0, total - reserved)


def check_stock(conn: sqlite3.Connection, item_id: int, quantity: int) -> bool:
    """检查库存是否充足"""
    available = get_available_quantity(conn, item_id)
    return available >= quantity


def reserve_stock(conn: sqlite3.Connection, item_id: int, quantity: int) -> bool:
    """
    检查库存是否充足。
    调用方负责事务管理——库存检查和记录创建在调用方的事务上下文中是原子操作。
    返回 True 表示库存充足，False 表示不足。
    """
    return check_stock(conn, item_id, quantity)


def release_stock(conn: sqlite3.Connection, item_id: int, quantity: int):
    """
    释放库存：将归还的物品数量从占用中移除。
    调用方负责确保事务一致性。
    """
    pass  # 库存是实时计算的，归还后自然释放，无需显式操作


def update_item_status(conn: sqlite3.Connection, item_id: int):
    """根据实时库存自动更新物品状态"""
    available = get_available_quantity(conn, item_id)
    item = conn.execute("SELECT total_quantity, status FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        return

    if item["status"] == "损坏":
        return  # 损坏状态不自动变

    if available <= 0:
        new_status = "租借中"
    else:
        new_status = "可用"

    if item["status"] != new_status:
        conn.execute(
            "UPDATE items SET status = ?, updated_at = datetime('now','localtime') WHERE id = ?",
            (new_status, item_id),
        )


def check_low_stock(conn: sqlite3.Connection) -> list:
    """检查所有库存低于阈值的物品，返回低库存物品列表"""
    rows = conn.execute("SELECT id, name, low_stock_threshold FROM items WHERE status != '损坏'").fetchall()
    low_stock = []
    for row in rows:
        total = get_total_quantity(conn, row["id"])
        available = get_available_quantity(conn, row["id"])
        if available <= row["low_stock_threshold"]:
            low_stock.append({
                "id": row["id"],
                "name": row["name"],
                "available": available,
                "total": total,
                "threshold": row["low_stock_threshold"],
            })
    return low_stock


def get_warehouse_stocks(conn: sqlite3.Connection, item_id: int) -> list:
    """获取物品在各仓库的库存分布"""
    rows = conn.execute(
        """SELECT ws.warehouse_id, w.name AS warehouse_name, ws.quantity
           FROM warehouse_stocks ws JOIN warehouses w ON ws.warehouse_id = w.id
           WHERE ws.item_id = ? AND ws.quantity > 0""",
        (item_id,),
    ).fetchall()
    return [dict(r) for r in rows]
