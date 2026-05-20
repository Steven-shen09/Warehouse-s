"""Warehouse-s FastAPI 应用工厂"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import init_db


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    app = FastAPI(
        title="Warehouse-s 物品租借系统",
        description="物品全生命周期管理、租借审批、归还追踪",
        version="1.4.0",
    )

    # 初始化数据库
    init_db()

    # 注册 API 路由
    from app.api import register_routes
    register_routes(app)

    # 挂载静态文件
    import os
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    return app
