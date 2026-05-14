"""API 路由注册"""
from fastapi import FastAPI
from app.api import auth, users, items, records, approvals, stats, audit_logs, frontend


def register_routes(app: FastAPI):
    """注册所有 API 路由"""
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(items.router)
    app.include_router(records.router)
    app.include_router(approvals.router)
    app.include_router(stats.router)
    app.include_router(audit_logs.router)
    # 前端页面路由（最后注册，避免覆盖 API 路径）
    app.include_router(frontend.router)
