"""从 SQLite 导出数据到 PostgreSQL — 一次性迁移"""
import sqlite3
from sqlalchemy import create_engine, text

SQLITE_PATH = "data/warehouse.db"
PG_URL = "postgresql+psycopg2://warehouse:warehouse123@localhost:5432/warehouse"


def migrate():
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    pg_engine = create_engine(PG_URL)

    with pg_engine.connect() as pg_conn:
        with pg_conn.begin():
            tables = ["users", "items", "warehouses", "warehouse_stocks",
                      "records", "approvals", "audit_logs",
                      "transfers", "inventory_counts", "inventory_count_items"]
            for table in tables:
                rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
                if not rows:
                    print(f"  {table}: 0 rows")
                    continue
                columns = rows[0].keys()
                col_list = ", ".join(columns)
                placeholders = ", ".join(f":{c}" for c in columns)
                for row in rows:
                    data = dict(row)
                    # 转换空字符串日期为 None
                    for k, v in data.items():
                        if isinstance(v, str) and v.strip() == "" and ("date" in k.lower() or k.endswith("_at")):
                            data[k] = None
                    try:
                        pg_conn.execute(text(
                            f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                        ), data)
                    except Exception as e:
                        print(f"  Skipping {table} row: {e}")
                print(f"  {table}: {len(rows)} rows")

    sqlite_conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    migrate()
