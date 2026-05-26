"""Test fixtures for Warehouse-s"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import create_app
from app.database import get_engine, init_db


@pytest.fixture(scope="session")
def app():
    """Create FastAPI test app"""
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    """Test client"""
    return TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def _reset_db():
    """Reset DB before each test"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.rollback()
        with conn.begin():
            conn.execute(text(
                "TRUNCATE TABLE consumable_records, asset_disposals, asset_assignments, "
                "purchase_order_items, asset_instances, inventory_count_items, approvals, "
                "records, purchase_orders, inventory_counts, transfers, warehouse_stocks, "
                "items, audit_logs, suppliers, departments, warehouses, users "
                "RESTART IDENTITY CASCADE"
            ))
    init_db()
    yield


@pytest.fixture(scope="function")
def admin_headers(client, _reset_db):
    """Admin auth headers"""
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(scope="function")
def user_headers(client, _reset_db):
    """User1 auth headers"""
    resp = client.post("/api/v1/auth/login", json={"username": "user1", "password": "123456"})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(scope="function")
def approver_headers(client, _reset_db):
    """Approver auth headers"""
    resp = client.post("/api/v1/auth/login", json={"username": "approver1", "password": "123456"})
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
