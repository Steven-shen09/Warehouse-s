"""PostgreSQL 数据库连接管理（SQLAlchemy Core）"""
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from app.config import settings

# ── 兼容性补丁：修复 SQLAlchemy 2.0.36 C 扩展在 Python 3.12 上 Row 对象不支持字符串 key 访问的 bug ──
from sqlalchemy.engine.row import Row
_orig_row_getitem = Row.__getitem__
_orig_row_iter = Row.__iter__


def _patched_row_getitem(self, key):
    if isinstance(key, (int, slice)):
        return _orig_row_getitem(self, key)
    return self._mapping[key]


def _patched_row_iter(self):
    return iter(self._mapping.items())


Row.__getitem__ = _patched_row_getitem
Row.__iter__ = _patched_row_iter

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            echo=False,
                    )
    return _engine


def get_db():
    """数据库连接依赖注入 — FastAPI Depends(get_db)"""
    with get_engine().connect() as conn:
        # 每条连接初始时确保无残留事务
        if conn.in_transaction():
            conn.rollback()
        yield conn


def init_db():
    """初始化数据库：创建所有表并插入种子数据"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.rollback()
        with conn.begin():
            _create_tables(conn)
            _seed_data(conn)


def _create_tables(conn):
    """创建所有数据表（PostgreSQL 语法）"""
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name VARCHAR(100) NOT NULL DEFAULT '',
            role VARCHAR(20) NOT NULL CHECK(role IN ('admin', 'approver', 'user')) DEFAULT 'user',
            email VARCHAR(200) DEFAULT '',
            phone VARCHAR(50) DEFAULT '',
            is_active SMALLINT NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            category VARCHAR(100) DEFAULT '',
            description TEXT DEFAULT '',
            location VARCHAR(200) DEFAULT '',
            image_url TEXT DEFAULT '',
            total_quantity INTEGER NOT NULL DEFAULT 1,
            status VARCHAR(20) NOT NULL CHECK(status IN ('可用', '租借中', '损坏')) DEFAULT '可用',
            value DOUBLE PRECISION NOT NULL DEFAULT 0,
            low_stock_threshold INTEGER DEFAULT 2,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS records (
            id SERIAL PRIMARY KEY,
            item_id INTEGER NOT NULL REFERENCES items(id),
            borrower_id INTEGER NOT NULL REFERENCES users(id),
            borrower_name VARCHAR(200) NOT NULL,
            contact VARCHAR(200) DEFAULT '',
            quantity INTEGER NOT NULL,
            borrow_date DATE NOT NULL,
            expected_return_date DATE NOT NULL,
            actual_return_date DATE DEFAULT NULL,
            reason TEXT DEFAULT '',
            return_notes TEXT DEFAULT '',
            status VARCHAR(20) NOT NULL CHECK(status IN ('待审核', '借出中', '已拒绝', '已归还', '逾期')) DEFAULT '待审核',
            approval_deadline TIMESTAMP DEFAULT NULL,
            original_record_id INTEGER DEFAULT NULL REFERENCES records(id),
            document_no VARCHAR(50) DEFAULT NULL,
            source_warehouse_id INTEGER DEFAULT NULL REFERENCES warehouses(id),
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS approvals (
            id SERIAL PRIMARY KEY,
            record_id INTEGER NOT NULL REFERENCES records(id),
            approver_id INTEGER NOT NULL REFERENCES users(id),
            action VARCHAR(20) NOT NULL CHECK(action IN ('approved', 'rejected')),
            comment TEXT DEFAULT '',
            ai_suggestion TEXT DEFAULT '',
            deadline TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            username VARCHAR(200) NOT NULL,
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(50) NOT NULL,
            target_id INTEGER NOT NULL,
            detail TEXT DEFAULT '',
            ip_address VARCHAR(50) DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS warehouses (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            location TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS warehouse_stocks (
            id SERIAL PRIMARY KEY,
            item_id INTEGER NOT NULL REFERENCES items(id),
            warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            quantity INTEGER NOT NULL DEFAULT 0,
            UNIQUE(item_id, warehouse_id)
        );

        CREATE TABLE IF NOT EXISTS transfers (
            id SERIAL PRIMARY KEY,
            item_id INTEGER NOT NULL REFERENCES items(id),
            from_warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            to_warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            quantity INTEGER NOT NULL,
            reason TEXT DEFAULT '',
            status VARCHAR(20) NOT NULL CHECK(status IN ('待审核', '已通过', '已驳回')) DEFAULT '待审核',
            document_no VARCHAR(50) DEFAULT NULL,
            created_by INTEGER NOT NULL REFERENCES users(id),
            approved_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS inventory_counts (
            id SERIAL PRIMARY KEY,
            warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            name VARCHAR(200) NOT NULL,
            status VARCHAR(20) NOT NULL CHECK(status IN ('进行中', '已完成', '已确认')) DEFAULT '进行中',
            created_by INTEGER NOT NULL REFERENCES users(id),
            completed_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS inventory_count_items (
            id SERIAL PRIMARY KEY,
            count_id INTEGER NOT NULL REFERENCES inventory_counts(id),
            item_id INTEGER NOT NULL REFERENCES items(id),
            expected_quantity INTEGER NOT NULL DEFAULT 0,
            actual_quantity INTEGER DEFAULT NULL,
            difference INTEGER DEFAULT NULL,
            notes TEXT DEFAULT '',
            counted_at TIMESTAMP DEFAULT NULL
        );
    """))

    # 索引
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_records_status ON records(status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_records_item_id ON records(item_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_records_borrower_id ON records(borrower_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_records_document_no ON records(document_no)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_approvals_record_id ON approvals(record_id)"))

    # 默认仓库
    existing = conn.execute(text("SELECT COUNT(*) FROM warehouses")).fetchone()[0]
    if existing == 0:
        conn.execute(text(
            "INSERT INTO warehouses (name, location, description) VALUES ('默认仓库', '', '系统自动创建的默认仓库')"
        ))


def _seed_data(conn):
    """插入预置种子数据"""
    from app.utils.security import hash_password

    existing = conn.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
    if existing > 0:
        return

    users_data = [
        {"id": 1, "username": "admin", "password_hash": hash_password("admin123"), "display_name": "管理员", "role": "admin", "email": "admin@example.com", "phone": "13800000001"},
        {"id": 2, "username": "approver1", "password_hash": hash_password("123456"), "display_name": "审核员李", "role": "approver", "email": "approver1@example.com", "phone": "13800000002"},
        {"id": 3, "username": "user1", "password_hash": hash_password("123456"), "display_name": "用户张", "role": "user", "email": "user1@example.com", "phone": "13800000003"},
    ]
    for u in users_data:
        conn.execute(text(
            "INSERT INTO users (id, username, password_hash, display_name, role, email, phone) "
            "VALUES (:id, :username, :password_hash, :display_name, :role, :email, :phone)"
        ), u)

    items_data = [
        {"name": "投影仪", "category": "电子设备", "description": "会议室用投影仪", "location": "A-101", "total_quantity": 5, "value": 1500.00},
        {"name": "笔记本电脑", "category": "电子设备", "description": "办公笔记本电脑", "location": "A-102", "total_quantity": 10, "value": 5000.00},
        {"name": "折叠椅", "category": "家具", "description": "可折叠办公椅", "location": "B-201", "total_quantity": 20, "value": 80.00},
        {"name": "白板", "category": "办公用品", "description": "可移动白板", "location": "B-202", "total_quantity": 8, "value": 200.00},
        {"name": "工具箱", "category": "工具", "description": "常用维修工具箱", "location": "C-301", "total_quantity": 3, "value": 300.00},
    ]
    for item in items_data:
        conn.execute(text(
            "INSERT INTO items (name, category, description, location, total_quantity, value) "
            "VALUES (:name, :category, :description, :location, :total_quantity, :value)"
        ), item)

    # 种子物品库存分配到默认仓库
    seed_items = conn.execute(text("SELECT id, total_quantity FROM items")).fetchall()
    for row in seed_items:
        conn.execute(text(
            "INSERT INTO warehouse_stocks (item_id, warehouse_id, quantity) VALUES (:iid, 1, :qty) ON CONFLICT DO NOTHING"
        ), {"iid": row[0], "qty": row[1]})


# 向后兼容 — 供 seed_test_data.py 等直接脚本使用
def get_connection():
    return get_engine().connect()
