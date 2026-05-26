"""API 路由注册"""
from fastapi import FastAPI
from app.api import auth, users, items, records, approvals, stats, audit_logs, warehouses, transfers, inventory_counts, frontend
from app.api import suppliers, departments, purchase_orders, assets, asset_disposals, consumable_records, warehouse_items


def register_routes(app: FastAPI):
    """注册所有 API 路由"""
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(items.router)
    app.include_router(records.router)
    app.include_router(approvals.router)
    app.include_router(stats.router)
    app.include_router(audit_logs.router)
    app.include_router(warehouses.router)
    app.include_router(transfers.router)
    app.include_router(inventory_counts.router)
    # 新增资产管理路由
    app.include_router(suppliers.router)
    app.include_router(departments.router)
    app.include_router(purchase_orders.router)
    app.include_router(assets.router)
    app.include_router(asset_disposals.router)
    app.include_router(consumable_records.router)
    app.include_router(warehouse_items.router)
    # 前端页面路由（最后注册，避免覆盖 API 路径）
    app.include_router(frontend.router)
