"""通用辅助函数"""
from datetime import datetime, timedelta
from sqlalchemy import text


def now_str() -> str:
    """返回当前本地时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    """返回当前日期字符串"""
    return datetime.now().strftime("%Y-%m-%d")


def deadline_str(hours: int = 24) -> str:
    """返回当前时间 + N 小时后的时间字符串"""
    return (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")


def parse_date(date_str: str) -> datetime:
    """将日期字符串解析为 datetime 对象"""
    return datetime.strptime(date_str, "%Y-%m-%d")


def is_overdue(expected_date_str: str) -> bool:
    """检查是否已超过预期日期"""
    expected = datetime.strptime(expected_date_str, "%Y-%m-%d")
    return datetime.now() > expected


def generate_document_no(conn):
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"DJ-{today}-"
    row = conn.execute(text(
        "SELECT MAX(document_no) FROM records WHERE document_no ~ :pat"
    ), {"pat": f"^{prefix}[0-9]+$"}).fetchone()
    if row and row[0]:
        try:
            seq = int(row[0].split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def generate_purchase_doc_no(conn) -> str:
    """生成采购入库单号：CG-YYYYMMDD-NNNN"""
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"CG-{today}-"
    row = conn.execute(text(
        "SELECT MAX(document_no) FROM purchase_orders WHERE document_no ~ :pat"
    ), {"pat": f"^{prefix}[0-9]+$"}).fetchone()
    if row and row[0]:
        try:
            seq = int(row[0].split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def generate_consumable_doc_no(conn) -> str:
    """生成消耗品领用单号：LY-YYYYMMDD-NNNN"""
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"LY-{today}-"
    row = conn.execute(text(
        "SELECT MAX(document_no) FROM consumable_records WHERE document_no ~ :pat"
    ), {"pat": f"^{prefix}[0-9]+$"}).fetchone()
    if row and row[0]:
        try:
            seq = int(row[0].split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def generate_disposal_doc_no(conn) -> str:
    """生成资产报废单号：BF-YYYYMMDD-NNNN"""
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"BF-{today}-"
    row = conn.execute(text(
        "SELECT MAX(document_no) FROM asset_disposals WHERE document_no ~ :pat"
    ), {"pat": f"^{prefix}[0-9]+$"}).fetchone()
    if row and row[0]:
        try:
            seq = int(row[0].split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"
