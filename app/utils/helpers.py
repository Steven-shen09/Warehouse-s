"""通用辅助函数"""
from datetime import datetime, timedelta


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


def generate_document_no(conn) -> str:
    """生成单据号: DJ-20260515-0001（每天从 0001 开始自增）"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"DJ-{today}-"
    row = conn.execute(
        "SELECT MAX(document_no) FROM records WHERE document_no LIKE ?",
        (f"{prefix}%",)
    ).fetchone()
    if row and row[0]:
        seq = int(row[0].split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"
