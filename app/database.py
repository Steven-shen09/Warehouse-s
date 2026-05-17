"""SQLite 数据库连接管理"""
import sqlite3
import os
from contextlib import contextmanager
from app.config import settings


def get_db_path() -> str:
    """获取数据库文件路径，确保目录存在"""
    db_path = settings.DATABASE_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path


def get_connection() -> sqlite3.Connection:
    """创建新的数据库连接"""
    conn = sqlite3.connect(get_db_path(), timeout=20, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """初始化数据库：创建所有表并插入种子数据"""
    conn = get_connection()
    try:
        _create_tables(conn)
        _seed_data(conn)
        conn.commit()
    finally:
        conn.close()


def _create_tables(conn: sqlite3.Connection):
    """创建所有数据表"""
    conn.executescript("""
        -- 用户表
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL CHECK(role IN ('admin', 'approver', 'user')) DEFAULT 'user',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        -- 物品表
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT DEFAULT '',
            description TEXT DEFAULT '',
            location TEXT DEFAULT '',
            image_url TEXT DEFAULT '',
            total_quantity INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL CHECK(status IN ('可用', '租借中', '损坏')) DEFAULT '可用',
            value REAL NOT NULL DEFAULT 0,
            low_stock_threshold INTEGER DEFAULT 2,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        -- 租借记录表
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id),
            borrower_id INTEGER NOT NULL REFERENCES users(id),
            borrower_name TEXT NOT NULL,
            contact TEXT DEFAULT '',
            quantity INTEGER NOT NULL,
            borrow_date TEXT NOT NULL,
            expected_return_date TEXT NOT NULL,
            actual_return_date TEXT DEFAULT NULL,
            reason TEXT DEFAULT '',
            return_notes TEXT DEFAULT '',
            status TEXT NOT NULL CHECK(status IN ('待审核', '借出中', '已拒绝', '已归还', '逾期')) DEFAULT '待审核',
            approval_deadline TEXT DEFAULT NULL,
            original_record_id INTEGER DEFAULT NULL REFERENCES records(id),
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        -- 审核记录表
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL REFERENCES records(id),
            approver_id INTEGER NOT NULL REFERENCES users(id),
            action TEXT NOT NULL CHECK(action IN ('approved', 'rejected')),
            comment TEXT DEFAULT '',
            ai_suggestion TEXT DEFAULT '',
            deadline TEXT DEFAULT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        -- 操作日志表
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            detail TEXT DEFAULT '',
            ip_address TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        -- 索引
        CREATE INDEX IF NOT EXISTS idx_records_status ON records(status);
        CREATE INDEX IF NOT EXISTS idx_records_item_id ON records(item_id);
        CREATE INDEX IF NOT EXISTS idx_records_borrower_id ON records(borrower_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
        CREATE INDEX IF NOT EXISTS idx_approvals_record_id ON approvals(record_id);
    """)

    # 迁移：添加单据号字段（兼容旧数据，允许 NULL）
    try:
        conn.execute("ALTER TABLE records ADD COLUMN document_no TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass  # 字段已存在

    conn.execute("CREATE INDEX IF NOT EXISTS idx_records_document_no ON records(document_no)")


def _seed_data(conn: sqlite3.Connection):
    """插入预置种子数据"""
    from app.utils.security import hash_password

    # 检查是否已有数据
    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing > 0:
        return

    # 预置用户
    users = [
        (1, "admin", hash_password("admin123"), "管理员", "admin", "admin@example.com", "13800000001"),
        (2, "approver1", hash_password("123456"), "审核员李", "approver", "approver1@example.com", "13800000002"),
        (3, "user1", hash_password("123456"), "用户张", "user", "user1@example.com", "13800000003"),
    ]
    conn.executemany(
        "INSERT INTO users (id, username, password_hash, display_name, role, email, phone) VALUES (?, ?, ?, ?, ?, ?, ?)",
        users,
    )

    # 预置物品
    items = [
        ("投影仪", "电子设备", "会议室用投影仪", "A-101", 5, 1500.00),
        ("笔记本电脑", "电子设备", "办公笔记本电脑", "A-102", 10, 5000.00),
        ("折叠椅", "家具", "可折叠办公椅", "B-201", 20, 80.00),
        ("白板", "办公用品", "可移动白板", "B-202", 8, 200.00),
        ("工具箱", "工具", "常用维修工具箱", "C-301", 3, 300.00),
    ]
    conn.executemany(
        "INSERT INTO items (name, category, description, location, total_quantity, value) VALUES (?, ?, ?, ?, ?, ?)",
        items,
    )
