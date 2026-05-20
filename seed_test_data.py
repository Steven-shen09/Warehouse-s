"""插入测试数据：多仓库、调拨、盘点"""
from app.database import get_connection, init_db
from datetime import datetime, timedelta

init_db()
conn = get_connection()

# ═══ 1. 新增仓库 ═══
warehouses = [
    ("A区主仓库", "A栋1楼", "主要物资存放区"),
    ("B区备品仓", "B栋2楼", "备品备件仓库"),
    ("C区工具间", "C栋地下1层", "工具设备存放"),
]
for name, loc, desc in warehouses:
    exists = conn.execute("SELECT id FROM warehouses WHERE name = ?", (name,)).fetchone()
    if not exists:
        conn.execute("INSERT INTO warehouses (name, location, description) VALUES (?, ?, ?)", (name, loc, desc))
        print(f"  新增仓库: {name}")
conn.commit()

all_wh = conn.execute("SELECT id, name FROM warehouses").fetchall()
wh_map = {w["name"]: w["id"] for w in all_wh}
print(f"仓库总数: {len(all_wh)}")

# ═══ 2. 新增物品 ═══
items_data = [
    ("饮水机", "电器", "美的 MYR926S 立式冷热饮水机", 8, 850.00),
    ("扫描仪", "电子设备", "富士通 FI-7160 高速文档扫描仪", 3, 3200.00),
    ("会议桌", "家具", "2.4m×1.2m 实木会议桌，配8把椅子", 2, 4800.00),
    ("无人机", "电子设备", "大疆 Mavic 3 航拍无人机", 4, 12800.00),
    ("标签打印机", "办公用品", "兄弟 PT-P900 电脑标签打印机", 5, 1200.00),
    ("电动螺丝刀", "工具", "博世 GSR 120-LI 12V 锂电螺丝刀", 10, 350.00),
    ("示波器", "仪器", "RIGOL DS1054Z 四通道数字示波器", 2, 5800.00),
    ("文件柜", "家具", "钢制四层抽屉文件柜 900×400×1800", 6, 1200.00),
]
for name, cat, desc, qty, price in items_data:
    exists = conn.execute("SELECT id FROM items WHERE name = ?", (name,)).fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO items (name, category, description, total_quantity, value) VALUES (?, ?, ?, ?, ?)",
            (name, cat, desc, qty, price),
        )
        print(f"  新增物品: {name}")
conn.commit()

all_items = conn.execute("SELECT id, name, total_quantity FROM items").fetchall()
print(f"物品总数: {len(all_items)}")

# ═══ 3. 分配分仓库存 ═══
for item in all_items:
    existing = conn.execute("SELECT id FROM warehouse_stocks WHERE item_id = ?", (item["id"],)).fetchone()
    if existing:
        continue
    conn.execute(
        "INSERT INTO warehouse_stocks (item_id, warehouse_id, quantity) VALUES (?, 1, ?)",
        (item["id"], item["total_quantity"]),
    )
    print(f"  {item['name']} → 默认仓库 ×{item['total_quantity']}")

# 部分物品加入B区仓库
b_items = [("饮水机", 3), ("电动螺丝刀", 5), ("标签打印机", 2)]
for name, qty in b_items:
    item = conn.execute("SELECT id FROM items WHERE name = ?", (name,)).fetchone()
    if item:
        conn.execute(
            "INSERT INTO warehouse_stocks (item_id, warehouse_id, quantity) VALUES (?, ?, ?)",
            (item["id"], wh_map["B区备品仓"], qty),
        )
        print(f"  {name} → B区备品仓 ×{qty}")
conn.commit()

# ═══ 4. 创建调拨记录 ═══
admin_id = conn.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1").fetchone()["id"]

def _doc_no(conn):
    today = datetime.now().strftime("%Y%m%d")
    count = conn.execute("SELECT COUNT(*) FROM transfers WHERE document_no LIKE ?", (f"DB-{today}-%",)).fetchone()[0]
    return f"DB-{today}-{count + 1:03d}"

transfer_items = [
    ("投影仪", wh_map["默认仓库"], wh_map["A区主仓库"], 2, "活动需要", "已通过"),
    ("笔记本电脑", wh_map["默认仓库"], wh_map["C区工具间"], 3, "研发部借用", "待审核"),
    ("折叠椅", wh_map["默认仓库"], wh_map["B区备品仓"], 5, "会议室备用", "已通过"),
    ("工具箱", wh_map["B区备品仓"], wh_map["A区主仓库"], 1, "维修移库", "已驳回"),
]
for name, fw, tw, qty, reason, status in transfer_items:
    item = conn.execute("SELECT id FROM items WHERE name = ?", (name,)).fetchone()
    if not item:
        continue
    exists = conn.execute(
        "SELECT id FROM transfers WHERE item_id = ? AND status = ? LIMIT 1", (item["id"], status)
    ).fetchone()
    if exists:
        continue
    doc = _doc_no(conn)
    conn.execute(
        """INSERT INTO transfers (item_id, from_warehouse_id, to_warehouse_id, quantity, reason, status, document_no, created_by, approved_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (item["id"], fw, tw, qty, reason, status, doc, admin_id, admin_id if status == "已通过" else None),
    )
    print(f"  调拨: {name} {fw}→{tw} ×{qty} [{status}] {doc}")
conn.commit()

# ═══ 5. 创建盘点记录 ═══
count = conn.execute("SELECT COUNT(*) FROM inventory_counts").fetchone()[0]
if count == 0:
    conn.execute(
        "INSERT INTO inventory_counts (warehouse_id, name, created_by) VALUES (?, ?, ?)",
        (wh_map["默认仓库"], "2026年5月 默认仓库例行盘点", admin_id),
    )
    cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    stocks = conn.execute(
        """SELECT ws.item_id, ws.quantity, i.name
           FROM warehouse_stocks ws JOIN items i ON ws.item_id = i.id
           WHERE ws.warehouse_id = ? AND ws.quantity > 0""",
        (wh_map["默认仓库"],),
    ).fetchall()

    for s in stocks:
        actual = s["quantity"]  # 大部分与实际一致
        if s["name"] == "笔记本电脑":
            actual = 180  # 模拟盘亏5台
        elif s["name"] == "折叠椅":
            actual = 17  # 模拟盘亏3把
        diff = actual - s["quantity"]
        conn.execute(
            "INSERT INTO inventory_count_items (count_id, item_id, expected_quantity, actual_quantity, difference, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (cid, s["item_id"], s["quantity"], actual, diff, "盘点差异" if diff != 0 else ""),
        )
    conn.commit()
    print(f"  盘点: ID={cid} 明细{len(stocks)}条 (含笔记本电脑盘亏5台、折叠椅盘亏3把)")

# ═══ 汇总 ═══
print()
print("═" * 40)
print(f"仓库: {conn.execute('SELECT COUNT(*) FROM warehouses').fetchone()[0]} 个")
print(f"物品: {conn.execute('SELECT COUNT(*) FROM items').fetchone()[0]} 个")
print(f"分仓库存: {conn.execute('SELECT COUNT(*) FROM warehouse_stocks').fetchone()[0]} 条")
print(f"调拨记录: {conn.execute('SELECT COUNT(*) FROM transfers').fetchone()[0]} 条")
print(f"盘点记录: {conn.execute('SELECT COUNT(*) FROM inventory_counts').fetchone()[0]} 条")
print(f"盘点明细: {conn.execute('SELECT COUNT(*) FROM inventory_count_items').fetchone()[0]} 条")
print("测试数据插入完成!")

conn.close()
