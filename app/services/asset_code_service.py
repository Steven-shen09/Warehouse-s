"""资产编号生成服务"""
from sqlalchemy import text


def generate_asset_code(conn, item: dict, purchase_date: str, batch_no: str, serial: int) -> str:
    """
    生成资产编号：{物品简称}-{采购日期}-{批次序号}-{批次内序号:04d}

    item: 物品行 dict {id, abbreviation, name}
    purchase_date: 采购日期字符串 (YYYYMMDD 或 date 对象)
    batch_no: 批次号
    serial: 批次内序号 (1-based)
    """
    abbr = item.get("abbreviation", "") or _auto_abbreviate(item.get("name", ""))

    if hasattr(purchase_date, "strftime"):
        date_str = purchase_date.strftime("%Y%m%d")
    else:
        date_str = str(purchase_date).replace("-", "")

    if not batch_no:
        batch_no = _compute_batch_serial(conn, item["id"], date_str)

    return f"{abbr}-{date_str}-{batch_no}-{serial:04d}"


def _auto_abbreviate(name: str) -> str:
    """从汉字名称提取拼音首字母作为简称（简化版：取前2个字符的首字母）"""
    import unicodedata
    result = []
    for ch in name:
        if "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿":
            # 汉字：取拼音首字母（简化处理：直接取 Unicode 序号映射）
            code = ord(ch)
            # 使用 pypinyin 库的替代方案：常见汉字首字母映射
            result.append(_hanzi_to_pinyin_initial(ch))
        elif ch.isalpha():
            result.append(ch.upper())
    abbr = "".join(result[:4])
    return abbr if abbr else "WP"  # WP = 物品


def _hanzi_to_pinyin_initial(ch: str) -> str:
    """简易汉字拼音首字母映射（覆盖常见汉字，后续可用 pypinyin 替代）"""
    # 常用汉字拼音首字母对照
    mapping = {
        "电": "D", "子": "Z", "设": "S", "备": "B",
        "投": "T", "影": "Y", "仪": "Y",
        "笔": "B", "记": "J", "本": "B", "脑": "N",
        "打": "D", "印": "Y", "机": "J",
        "桌": "Z", "椅": "Y", "柜": "G",
        "工": "G", "具": "J", "箱": "X",
        "白": "B", "板": "B",
        "家": "J", "具": "J",
        "办": "B", "公": "G", "用": "Y", "品": "P",
        "折": "Z", "叠": "D",
        "纸": "Z",
        "文": "W", "件": "J",
        "车": "C", "辆": "L",
        "空": "K", "调": "T",
        "风": "F", "扇": "S",
        "手": "S", "机": "J",
        "平": "P",
        "服": "F", "装": "Z",
        "器": "Q",
        "材": "C", "料": "L",
        "消": "X", "耗": "H",
        "维": "W", "修": "X",
    }
    return mapping.get(ch, ch[0].upper() if ch.isascii() else "X")


def _compute_batch_serial(conn, item_id: int, purchase_date_str: str) -> str:
    """计算该物品在同日期的第几批采购"""
    count = conn.execute(text(
        "SELECT COUNT(DISTINCT poi.purchase_order_id) FROM purchase_order_items poi "
        "JOIN purchase_orders po ON poi.purchase_order_id = po.id "
        "WHERE poi.item_id = :iid AND po.purchase_date = CAST(:pdate AS DATE)"
    ), {"iid": item_id, "pdate": purchase_date_str}).fetchone()[0]
    return f"{count:03d}"


def check_asset_code_exists(conn, asset_code: str) -> bool:
    """检查资产编号是否已存在"""
    if not asset_code or not asset_code.strip():
        return False
    row = conn.execute(text(
        "SELECT COUNT(*) FROM asset_instances WHERE asset_code = :code"
    ), {"code": asset_code}).fetchone()
    return row[0] > 0


def batch_generate_codes(conn):
    """为所有 asset_code 为空的资产实例批量生成编号"""
    rows = conn.execute(text(
        "SELECT ai.id, ai.item_id, ai.purchase_date, ai.purchase_order_item_id, "
        "i.name, i.abbreviation "
        "FROM asset_instances ai JOIN items i ON ai.item_id = i.id "
        "WHERE ai.asset_code IS NULL OR ai.asset_code = ''"
    )).fetchall()

    generated = 0
    for row in rows:
        item = {"id": row["item_id"], "name": row["name"], "abbreviation": row["abbreviation"]}
        purchase_date = row["purchase_date"]
        if hasattr(purchase_date, "strftime"):
            date_str = purchase_date.strftime("%Y%m%d")
        else:
            date_str = str(purchase_date).replace("-", "")

        batch_no = _compute_batch_serial(conn, row["item_id"], date_str)

        # 查找该批次已有多少资产实例
        existing_count = conn.execute(text(
            "SELECT COUNT(*) FROM asset_instances "
            "WHERE item_id = :iid AND purchase_date = :pd::date AND asset_code IS NOT NULL AND asset_code != ''"
        ), {"iid": row["item_id"], "pd": date_str}).fetchone()[0]

        code = generate_asset_code(conn, item, purchase_date, batch_no, existing_count + 1)
        conn.execute(text(
            "UPDATE asset_instances SET asset_code = :code, updated_at = NOW() WHERE id = :aid"
        ), {"code": code, "aid": row["id"]})
        generated += 1

    return generated
