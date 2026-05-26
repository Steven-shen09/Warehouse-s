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


def _extend_existing_tables(conn):
    """为已有表添加新字段（幂等操作）"""
    # items 表扩展
    conn.execute(text(
        "ALTER TABLE items ADD COLUMN IF NOT EXISTS item_type VARCHAR(20) "
        "CHECK(item_type IN ('consumable', 'tool', 'fixed_asset')) DEFAULT 'tool'"
    ))
    conn.execute(text("ALTER TABLE items ADD COLUMN IF NOT EXISTS abbreviation VARCHAR(20) DEFAULT ''"))
    conn.execute(text("ALTER TABLE items ADD COLUMN IF NOT EXISTS specification VARCHAR(200) DEFAULT ''"))
    conn.execute(text("ALTER TABLE items ADD COLUMN IF NOT EXISTS brand VARCHAR(100) DEFAULT ''"))
    conn.execute(text("ALTER TABLE items ADD COLUMN IF NOT EXISTS department_id INTEGER REFERENCES departments(id)"))

    # warehouses 表扩展
    conn.execute(text(
        "ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS warehouse_type VARCHAR(20) "
        "CHECK(warehouse_type IN ('consumable', 'tool', 'fixed_asset', 'mixed')) DEFAULT 'mixed'"
    ))

    # asset_assignments 扩展：支持待审核/已驳回状态
    conn.execute(text(
        "ALTER TABLE asset_assignments DROP CONSTRAINT IF EXISTS asset_assignments_status_check"
    ))
    conn.execute(text(
        "ALTER TABLE asset_assignments ADD CONSTRAINT asset_assignments_status_check "
        "CHECK(status IN ('待审核', '使用中', '已交回', '已驳回'))"
    ))

    # consumable_records 修复：移除 document_no 唯一约束，支持批量单据
    conn.execute(text(
        "ALTER TABLE consumable_records DROP CONSTRAINT IF EXISTS consumable_records_document_no_key"
    ))

    # asset_assignments: 允许手动输入使用人/部门名称
    conn.execute(text("ALTER TABLE asset_assignments ALTER COLUMN assigned_to_user_id DROP NOT NULL"))
    conn.execute(text("ALTER TABLE asset_assignments ALTER COLUMN assigned_to_department_id DROP NOT NULL"))
    conn.execute(text("ALTER TABLE asset_assignments DROP CONSTRAINT IF EXISTS asset_assignments_assigned_to_department_id_fkey"))
    conn.execute(text("ALTER TABLE asset_assignments DROP CONSTRAINT IF EXISTS asset_assignments_assigned_to_user_id_fkey"))
    conn.execute(text("ALTER TABLE asset_assignments ADD COLUMN IF NOT EXISTS user_name VARCHAR(100) DEFAULT ''"))
    conn.execute(text("ALTER TABLE asset_assignments ADD COLUMN IF NOT EXISTS department_name VARCHAR(100) DEFAULT ''"))
    conn.execute(text("ALTER TABLE asset_assignments ADD COLUMN IF NOT EXISTS document_no VARCHAR(50) DEFAULT ''"))

    # asset_instances 扩展：支持手动输入姓名
    conn.execute(text("ALTER TABLE asset_instances ADD COLUMN IF NOT EXISTS user_name VARCHAR(100) DEFAULT ''"))
    conn.execute(text("ALTER TABLE asset_instances ADD COLUMN IF NOT EXISTS department_name VARCHAR(100) DEFAULT ''"))


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

        -- 部门表
        CREATE TABLE IF NOT EXISTS departments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            parent_id INTEGER REFERENCES departments(id),
            manager_id INTEGER REFERENCES users(id),
            description TEXT DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        -- 供应商表
        CREATE TABLE IF NOT EXISTS suppliers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            contact_person VARCHAR(100) DEFAULT '',
            phone VARCHAR(50) DEFAULT '',
            email VARCHAR(200) DEFAULT '',
            address TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        -- 采购入库单
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id SERIAL PRIMARY KEY,
            document_no VARCHAR(50) NOT NULL UNIQUE,
            supplier_id INTEGER REFERENCES suppliers(id),
            warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            status VARCHAR(20) NOT NULL CHECK(status IN ('待审核', '已入库', '已取消')) DEFAULT '待审核',
            total_amount DOUBLE PRECISION NOT NULL DEFAULT 0,
            purchase_date DATE NOT NULL,
            notes TEXT DEFAULT '',
            created_by INTEGER NOT NULL REFERENCES users(id),
            approved_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        -- 采购入库明细
        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id SERIAL PRIMARY KEY,
            purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id),
            item_id INTEGER NOT NULL REFERENCES items(id),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price DOUBLE PRECISION NOT NULL DEFAULT 0,
            batch_no VARCHAR(50) DEFAULT '',
            production_date DATE DEFAULT NULL,
            expiry_date DATE DEFAULT NULL,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        -- 固定资产实例
        CREATE TABLE IF NOT EXISTS asset_instances (
            id SERIAL PRIMARY KEY,
            item_id INTEGER NOT NULL REFERENCES items(id),
            asset_code VARCHAR(50) UNIQUE,
            serial_number VARCHAR(100) DEFAULT '',
            status VARCHAR(20) NOT NULL CHECK(status IN ('在库', '使用中', '维修中', '已报废')) DEFAULT '在库',
            current_user_id INTEGER REFERENCES users(id),
            current_department_id INTEGER REFERENCES departments(id),
            purchase_date DATE NOT NULL,
            purchase_order_item_id INTEGER REFERENCES purchase_order_items(id),
            warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            notes TEXT DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        -- 固定资产领用/交回记录
        CREATE TABLE IF NOT EXISTS asset_assignments (
            id SERIAL PRIMARY KEY,
            asset_instance_id INTEGER NOT NULL REFERENCES asset_instances(id),
            assigned_to_user_id INTEGER,
            assigned_to_department_id INTEGER,
            assignment_date DATE NOT NULL,
            expected_return_date DATE,
            actual_return_date DATE,
            status VARCHAR(20) NOT NULL CHECK(status IN ('待审核', '使用中', '已交回', '已驳回')) DEFAULT '待审核',
            notes TEXT DEFAULT '',
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        -- 固定资产报废单
        CREATE TABLE IF NOT EXISTS asset_disposals (
            id SERIAL PRIMARY KEY,
            document_no VARCHAR(50) NOT NULL UNIQUE,
            asset_instance_id INTEGER NOT NULL REFERENCES asset_instances(id),
            disposal_type VARCHAR(20) NOT NULL CHECK(disposal_type IN ('报废', '出售', '捐赠', '丢失')),
            reason TEXT NOT NULL DEFAULT '',
            status VARCHAR(20) NOT NULL CHECK(status IN ('待审核', '已通过', '已驳回')) DEFAULT '待审核',
            disposal_date DATE,
            residual_value DOUBLE PRECISION DEFAULT 0,
            notes TEXT DEFAULT '',
            created_by INTEGER NOT NULL REFERENCES users(id),
            approved_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        -- 消耗品领用记录
        CREATE TABLE IF NOT EXISTS consumable_records (
            id SERIAL PRIMARY KEY,
            document_no VARCHAR(50) NOT NULL,
            item_id INTEGER NOT NULL REFERENCES items(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            pickup_date DATE NOT NULL,
            reason TEXT DEFAULT '',
            status VARCHAR(20) NOT NULL CHECK(status IN ('待审核', '已领取', '已拒绝')) DEFAULT '待审核',
            source_warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            created_by INTEGER NOT NULL REFERENCES users(id),
            approved_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """))

    # ── 扩展已有表字段（在新表创建之后，确保外键引用表已存在）──
    _extend_existing_tables(conn)

    # 索引
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_records_status ON records(status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_records_item_id ON records(item_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_records_borrower_id ON records(borrower_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_records_document_no ON records(document_no)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_approvals_record_id ON approvals(record_id)"))

    # 新表索引
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_departments_parent ON departments(parent_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_po_items_order ON purchase_order_items(purchase_order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_po_items_item ON purchase_order_items(item_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_po_doc_no ON purchase_orders(document_no)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_item ON asset_instances(item_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_asset_code ON asset_instances(asset_code)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_status ON asset_instances(status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_department ON asset_instances(current_department_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_user ON asset_instances(current_user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ai_warehouse ON asset_instances(warehouse_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_aa_asset ON asset_assignments(asset_instance_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_aa_user ON asset_assignments(assigned_to_user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_asset ON asset_disposals(asset_instance_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_doc_no ON asset_disposals(document_no)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_status ON asset_disposals(status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cr_item ON consumable_records(item_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cr_user ON consumable_records(user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cr_doc_no ON consumable_records(document_no)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cr_status ON consumable_records(status)"))

    # ── 功能性仓库（首次初始化时创建）──
    existing = conn.execute(text("SELECT COUNT(*) FROM warehouses")).fetchone()[0]
    if existing == 0:
        warehouses_data = [
            ("耗材仓库", "consumable", "消耗品存放仓库，用户领取不归还"),
            ("工具仓库", "tool", "工具类物品租借仓库，需归还"),
            ("固定资产仓库", "fixed_asset", "固定资产存放仓库，领用需登记"),
            ("默认仓库", "mixed", "通用仓库"),
        ]
        for name, wtype, desc in warehouses_data:
            conn.execute(text(
                "INSERT INTO warehouses (name, warehouse_type, location, description) VALUES (:n, :wt, '', :d)"
            ), {"n": name, "wt": wtype, "d": desc})


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

    # 种子供应商
    suppliers_data = [
        {"name": "京东企业购", "contact_person": "李经理", "phone": "400-001-0001"},
        {"name": "联想商用", "contact_person": "赵经理", "phone": "400-100-8000"},
        {"name": "得力办公", "contact_person": "陈代表", "phone": "0571-88889999"},
    ]
    for s in suppliers_data:
        conn.execute(text(
            "INSERT INTO suppliers (name, contact_person, phone) VALUES (:n, :c, :p)"
        ), {"n": s["name"], "c": s["contact_person"], "p": s["phone"]})

    items_data = [
        {"name": "投影仪", "category": "电子设备", "description": "会议室用投影仪", "location": "A-101", "total_quantity": 5, "value": 1500.00, "item_type": "tool"},
        {"name": "笔记本电脑", "category": "电子设备", "description": "办公笔记本电脑", "location": "A-102", "total_quantity": 10, "value": 5000.00, "item_type": "fixed_asset"},
        {"name": "折叠椅", "category": "家具", "description": "可折叠办公椅", "location": "B-201", "total_quantity": 20, "value": 80.00, "item_type": "tool"},
        {"name": "白板", "category": "办公用品", "description": "可移动白板", "location": "B-202", "total_quantity": 8, "value": 200.00, "item_type": "fixed_asset"},
        {"name": "工具箱", "category": "工具", "description": "常用维修工具箱", "location": "C-301", "total_quantity": 3, "value": 300.00, "item_type": "tool"},
        {"name": "A4打印纸", "category": "办公用品", "description": "A4复印纸 70g", "location": "", "total_quantity": 50, "value": 25.00, "item_type": "consumable"},
    ]
    for item in items_data:
        conn.execute(text(
            "INSERT INTO items (name, category, description, location, total_quantity, value, item_type) "
            "VALUES (:name, :category, :description, :location, :total_quantity, :value, :item_type)"
        ), item)

    # 种子物品库存按类型分配到对应仓库
    # warehouse_id: 1=耗材仓库, 2=工具仓库, 3=固定资产仓库, 4=默认仓库
    seed_items = conn.execute(text("SELECT id, total_quantity, item_type FROM items")).fetchall()
    for row in seed_items:
        it = row[2] if row[2] else "tool"
        if it == "consumable":
            wh_id = 1
        elif it == "fixed_asset":
            wh_id = 3
        else:
            wh_id = 2  # tool → 工具仓库
        conn.execute(text(
            "INSERT INTO warehouse_stocks (item_id, warehouse_id, quantity) VALUES (:iid, :wid, :qty) ON CONFLICT DO NOTHING"
        ), {"iid": row[0], "wid": wh_id, "qty": row[1]})

        # 固定资产：按数量创建 asset_instances 记录
        if it == "fixed_asset" and row[1] > 0:
            for _ in range(row[1]):
                conn.execute(text(
                    "INSERT INTO asset_instances (item_id, asset_code, status, purchase_date, warehouse_id) "
                    "VALUES (:iid, NULL, '在库', CURRENT_DATE, :wid)"
                ), {"iid": row[0], "wid": wh_id})


# 向后兼容 — 供 seed_test_data.py 等直接脚本使用
def get_connection():
    return get_engine().connect()
