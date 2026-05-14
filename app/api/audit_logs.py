"""操作日志路由"""
from fastapi import APIRouter, Depends
from app.api.deps import get_db, get_current_user, require_role
from app.services.audit_service import get_logs

router = APIRouter(prefix="/api/v1/logs", tags=["操作日志"])


@router.get("/")
def list_logs(
    page: int = 1,
    page_size: int = 50,
    action: str = "",
    target_type: str = "",
    username: str = "",
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """操作日志列表"""
    return get_logs(conn, page, page_size, action, target_type, username)
