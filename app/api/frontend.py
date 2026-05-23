"""前端页面路由：渲染 Jinja2 模板"""
import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text
from app.utils.security import verify_token

router = APIRouter(tags=["前端"])
security = HTTPBearer(auto_error=False)

# Jinja2 环境（模块级单例）
_templates_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "frontend", "templates"
)
_jinja_env = Environment(loader=FileSystemLoader(_templates_dir), autoescape=True)


async def get_optional_user(request: Request):
    """尝试获取当前登录用户：先查 Cookie，再查 Authorization header"""
    from app.database import get_connection
    token = request.cookies.get("warehouse_token")
    if not token:
        try:
            credentials = await security(request)
            if credentials:
                token = credentials.credentials
        except Exception:
            pass
    if not token:
        return None

    try:
        payload = verify_token(token)
    except Exception:
        return None

    conn = get_connection()
    try:
        user = conn.execute(text(
            "SELECT id, username, display_name, role FROM users WHERE id = :uid AND is_active = 1"
        ), {"uid": int(payload["sub"])}).fetchone()
        if user:
            u = dict(user)
            role_map = {"admin": "管理员", "approver": "审核员", "user": "普通用户"}
            u["role_display"] = role_map.get(u["role"], u["role"])
            return u
    finally:
        conn.close()
    return None


def _render(request: Request, name: str, ctx: dict = None) -> HTMLResponse:
    """渲染 Jinja2 模板"""
    template = _jinja_env.get_template(name)
    context = ctx or {}
    context["request"] = request
    html = template.render(context)
    return HTMLResponse(content=html)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = await get_optional_user(request)
    if user:
        return RedirectResponse(url="/dashboard")
    return _render(request, "login.html")


@router.get("/debug/auth")
async def debug_auth(request: Request):
    """调试端点：逐步诊断认证流程"""
    from app.database import get_connection
    from app.utils.security import verify_token as vt
    cookies = dict(request.cookies)
    token = request.cookies.get("warehouse_token", "")

    steps = {}
    if token:
        try:
            payload = vt(token)
            steps["verify"] = "OK"
            steps["payload"] = payload
        except Exception as e:
            steps["verify"] = f"FAIL: {e}"
            payload = None
    else:
        steps["verify"] = "SKIP"
        payload = None

    if payload:
        conn = get_connection()
        try:
            steps["db_connect"] = "OK"
            user = conn.execute(text(
                "SELECT id, username, display_name, role FROM users WHERE id = :uid AND is_active = 1"
            ), {"uid": int(payload["sub"])}).fetchone()
            steps["user_found"] = user is not None
            if user:
                steps["user_data"] = dict(user)
        except Exception as e:
            steps["db_error"] = str(e)
        finally:
            conn.close()

    return {
        "cookies_received": cookies,
        "token_present": bool(token),
        "token_preview": token[:30] + "..." if token else "",
        "steps": steps,
    }


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = await get_optional_user(request)
    if user:
        return RedirectResponse(url="/dashboard")
    return _render(request, "login.html")


@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login")
    resp.delete_cookie("warehouse_token")
    return resp


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    user = await get_optional_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return _render(request, "dashboard.html", {"current_user": user, "active_page": "dashboard"})


@router.get("/items", response_class=HTMLResponse)
async def items_page(request: Request):
    user = await get_optional_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return _render(request, "pages/items.html", {"current_user": user, "active_page": "items"})


@router.get("/items/{item_id}", response_class=HTMLResponse)
async def item_detail_page(request: Request, item_id: int):
    user = await get_optional_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return _render(request, "pages/items.html", {"current_user": user, "active_page": "items"})


@router.get("/records", response_class=HTMLResponse)
async def records_page(request: Request):
    user = await get_optional_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return _render(request, "pages/records.html", {"current_user": user, "active_page": "records"})


@router.get("/approvals", response_class=HTMLResponse)
async def approvals_page(request: Request):
    user = await get_optional_user(request)
    if not user or user["role"] not in ("admin", "approver"):
        return RedirectResponse(url="/dashboard")
    return _render(request, "pages/approvals.html", {"current_user": user, "active_page": "approvals"})


@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    user = await get_optional_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/dashboard")
    return _render(request, "pages/users.html", {"current_user": user, "active_page": "users"})


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    user = await get_optional_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/dashboard")
    return _render(request, "pages/logs.html", {"current_user": user, "active_page": "logs"})


@router.get("/warehouses", response_class=HTMLResponse)
async def warehouses_page(request: Request):
    user = await get_optional_user(request)
    if not user:
        return RedirectResponse(url="/login")
    if user["role"] not in ("admin", "approver"):
        return RedirectResponse(url="/dashboard")
    return _render(request, "pages/warehouses.html", {"current_user": user, "active_page": "warehouses"})


@router.get("/transfers", response_class=HTMLResponse)
async def transfers_page(request: Request):
    user = await get_optional_user(request)
    if not user:
        return RedirectResponse(url="/login")
    if user["role"] not in ("admin", "approver"):
        return RedirectResponse(url="/dashboard")
    return _render(request, "pages/transfers.html", {"current_user": user, "active_page": "transfers"})


@router.get("/inventory-counts", response_class=HTMLResponse)
async def inventory_counts_page(request: Request):
    user = await get_optional_user(request)
    if not user:
        return RedirectResponse(url="/login")
    if user["role"] not in ("admin", "approver"):
        return RedirectResponse(url="/dashboard")
    return _render(request, "pages/inventory_counts.html", {"current_user": user, "active_page": "inventory-counts"})


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    user = await get_optional_user(request)
    return _render(request, "pages/about.html", {"current_user": user, "active_page": "about"})
