"""固定资产管理路由"""
from typing import Optional
from sqlalchemy import text
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from app.api.deps import get_db, get_current_user, require_role
from app.services.asset_service import (
    assign_asset, return_asset, transfer_asset,
    repair_asset, repair_done_asset,
    request_assign_asset, request_batch_assign_asset,
)
from app.services.asset_code_service import check_asset_code_exists, batch_generate_codes

router = APIRouter(prefix="/api/v1/assets", tags=["固定资产管理"])


@router.get("/")
def list_assets(
    status: str = "",
    department_id: int = Query(default=None),
    keyword: str = "",
    item_id: int = Query(default=None),
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """固定资产实例列表"""
    where = "WHERE ai.status != '在库'"
    params = {}
    if status:
        where += " AND ai.status = :st"
        params["st"] = status
    if department_id is not None:
        where += " AND ai.current_department_id = :did"
        params["did"] = department_id
    if item_id is not None:
        where += " AND ai.item_id = :iid"
        params["iid"] = item_id
    if keyword:
        where += " AND (i.name LIKE :kw OR ai.asset_code LIKE :kw2 OR ai.serial_number LIKE :kw3)"
        params["kw"] = f"%{keyword}%"
        params["kw2"] = f"%{keyword}%"
        params["kw3"] = f"%{keyword}%"

    total = conn.execute(text(
        f"SELECT COUNT(*) FROM asset_instances ai JOIN items i ON ai.item_id = i.id {where}"
    ), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = conn.execute(text(
        f"SELECT ai.*, i.name AS item_name, i.category, i.specification, i.brand, "
        f"COALESCE(u.display_name, ai.user_name) AS user_name, "
        f"COALESCE(d.name, ai.department_name) AS department_name, "
        f"(SELECT aa.assignment_date FROM asset_assignments aa "
        f" WHERE aa.asset_instance_id = ai.id AND aa.status = '使用中' "
        f" ORDER BY aa.id DESC LIMIT 1) AS assignment_date "
        f"FROM asset_instances ai "
        f"JOIN items i ON ai.item_id = i.id "
        f"LEFT JOIN departments d ON ai.current_department_id = d.id "
        f"LEFT JOIN users u ON ai.current_user_id = u.id "
        f"{where} ORDER BY ai.id DESC LIMIT :limit OFFSET :offset"
    ), params).fetchall()

    return {"assets": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/ledger")
def asset_ledger(
    status: str = "",
    department_id: int = Query(default=None),
    item_type: str = "",
    keyword: str = "",
    page: int = 1,
    page_size: int = 50,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """资产台账（含更多字段）"""
    where = "WHERE ai.status != '在库'"
    params = {}
    if status:
        where += " AND ai.status = :st"
        params["st"] = status
    if department_id is not None:
        where += " AND ai.current_department_id = :did"
        params["did"] = department_id
    if item_type:
        where += " AND i.item_type = :it"
        params["it"] = item_type
    if keyword:
        where += " AND (i.name LIKE :kw OR ai.asset_code LIKE :kw2)"
        params["kw"] = f"%{keyword}%"
        params["kw2"] = f"%{keyword}%"

    total = conn.execute(text(
        f"SELECT COUNT(*) FROM asset_instances ai JOIN items i ON ai.item_id = i.id {where}"
    ), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = conn.execute(text(
        f"SELECT ai.*, i.name AS item_name, i.category, i.specification, i.brand, "
        f"i.item_type, i.value, "
        f"d.name AS department_name, u.display_name AS user_name, "
        f"w.name AS warehouse_name "
        f"FROM asset_instances ai "
        f"JOIN items i ON ai.item_id = i.id "
        f"LEFT JOIN departments d ON ai.current_department_id = d.id "
        f"LEFT JOIN users u ON ai.current_user_id = u.id "
        f"LEFT JOIN warehouses w ON ai.warehouse_id = w.id "
        f"{where} ORDER BY ai.id DESC LIMIT :limit OFFSET :offset"
    ), params).fetchall()

    return {"assets": [dict(r) for r in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/check-code")
def check_code(
    code: str = Query(...),
    exclude_id: int = Query(default=None),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """检查资产编号是否已存在"""
    exists = check_asset_code_exists(conn, code)
    if exists and exclude_id:
        current = conn.execute(text(
            "SELECT id FROM asset_instances WHERE id = :aid AND asset_code = :code"
        ), {"aid": exclude_id, "code": code}).fetchone()
        exists = current is None
    return {"exists": exists}


@router.post("/batch-generate-codes")
def batch_generate(
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """批量为空编号资产生成编号"""
    conn.rollback()
    with conn.begin():
        count = batch_generate_codes(conn)
    return {"message": f"已为 {count} 件资产生成编号"}


@router.post("/{asset_id}/request-assign")
def do_request_assign(
    asset_id: int,
    assigned_to_user_id: int = Query(default=None),
    assigned_to_department_id: int = Query(default=None),
    user_name: str = Query(default=""),
    department_name: str = Query(default=""),
    assignment_date: Optional[date] = Query(default=None),
    expected_return_date: Optional[date] = Query(default=None),
    notes: str = Query(default=""),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """用户发起固产领用申请（支持手动输入使用人和部门名称）"""
    conn.rollback()
    with conn.begin():
        try:
            result = request_assign_asset(
                conn, asset_id,
                assigned_to_user_id or current_user["id"],
                assigned_to_department_id or None,
                expected_return_date,
                notes, current_user["id"], user_name, department_name,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/batch-request-assign")
def do_batch_request_assign(
    asset_ids: str = Query(..., description="逗号分隔的资产ID列表"),
    user_name: str = Query(default=""),
    department_name: str = Query(default=""),
    assignment_date: Optional[date] = Query(default=None),
    notes: str = Query(default=""),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """批量提交固产领用申请（同一单据号）"""
    try:
        ids = [int(x.strip()) for x in asset_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="资产ID格式错误")
    if not ids:
        raise HTTPException(status_code=400, detail="请选择要领用的资产")
    conn.rollback()
    with conn.begin():
        try:
            result = request_batch_assign_asset(
                conn, ids, current_user["id"], None,
                assignment_date, notes, current_user["id"],
                user_name, department_name,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return result


@router.get("/{asset_id}")
def get_asset(
    asset_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """固定资产详情（含领用历史）"""
    asset = conn.execute(text(
        "SELECT ai.*, i.name AS item_name, i.category, i.specification, i.brand, i.value, "
        "COALESCE(u.display_name, ai.user_name) AS user_name, "
        "COALESCE(d.name, ai.department_name) AS department_name, "
        "(SELECT aa.assignment_date FROM asset_assignments aa "
        " WHERE aa.asset_instance_id = ai.id AND aa.status = '使用中' "
        " ORDER BY aa.id DESC LIMIT 1) AS assignment_date "
        "FROM asset_instances ai "
        "JOIN items i ON ai.item_id = i.id "
        "LEFT JOIN departments d ON ai.current_department_id = d.id "
        "LEFT JOIN users u ON ai.current_user_id = u.id "
        "WHERE ai.id = :aid"
    ), {"aid": asset_id}).fetchone()
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")

    d = dict(asset)
    # 领用历史
    assignments = conn.execute(text(
        "SELECT aa.*, u.display_name AS user_name, d.name AS department_name "
        "FROM asset_assignments aa "
        "LEFT JOIN users u ON aa.assigned_to_user_id = u.id "
        "LEFT JOIN departments d ON aa.assigned_to_department_id = d.id "
        "WHERE aa.asset_instance_id = :aid ORDER BY aa.id DESC"
    ), {"aid": asset_id}).fetchall()
    d["assignments"] = [dict(a) for a in assignments]
    return d


@router.put("/{asset_id}")
def update_asset(
    asset_id: int,
    asset_code: str = Query(default=None, max_length=50),
    serial_number: str = Query(default=None, max_length=100),
    notes: str = Query(default=None),
    current_user_id: int = Query(default=None),
    current_department_id: int = Query(default=None),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """更新资产信息（编号、序列号、使用人、部门等）"""
    existing = conn.execute(text("SELECT id, status FROM asset_instances WHERE id = :aid"), {"aid": asset_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="资产不存在")

    updates = {}
    if asset_code is not None:
        if asset_code and check_asset_code_exists(conn, asset_code):
            # 排除当前资产的编号
            current_code = conn.execute(text(
                "SELECT asset_code FROM asset_instances WHERE id = :aid"
            ), {"aid": asset_id}).fetchone()["asset_code"]
            if asset_code != current_code:
                raise HTTPException(status_code=400, detail="资产编号已存在")
        updates["asset_code"] = asset_code
    if serial_number is not None:
        updates["serial_number"] = serial_number
    if notes is not None:
        updates["notes"] = notes
    if current_user_id is not None:
        updates["current_user_id"] = current_user_id
    if current_department_id is not None:
        updates["current_department_id"] = current_department_id

    if updates:
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        params = dict(updates)
        params["aid"] = asset_id
        conn.rollback()
        with conn.begin():
            conn.execute(text(
                f"UPDATE asset_instances SET {set_clause}, updated_at = NOW() WHERE id = :aid"
            ), params)

    return {"message": "资产信息更新成功"}


@router.post("/{asset_id}/assign")
def do_assign(
    asset_id: int,
    assigned_to_user_id: int = Query(...),
    assigned_to_department_id: int = Query(...),
    assignment_date: date = Query(default=None),
    expected_return_date: Optional[date] = Query(default=None),
    notes: str = Query(default=""),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """领用固定资产"""
    if assignment_date is None:
        from datetime import date as dt_date
        assignment_date = dt_date.today()
    conn.rollback()
    with conn.begin():
        try:
            assign_asset(
                conn, asset_id, assigned_to_user_id, assigned_to_department_id,
                assignment_date, expected_return_date, notes, current_user["id"]
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "资产领用成功"}


@router.post("/{asset_id}/return")
def do_return(
    asset_id: int,
    return_date: date = Query(default=None),
    notes: str = Query(default=""),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """交回固定资产"""
    if return_date is None:
        from datetime import date as dt_date
        return_date = dt_date.today()
    conn.rollback()
    with conn.begin():
        try:
            return_asset(conn, asset_id, return_date, notes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "资产已交回"}


@router.post("/{asset_id}/transfer")
def do_transfer(
    asset_id: int,
    new_user_id: int = Query(...),
    new_department_id: int = Query(...),
    notes: str = Query(default=""),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """转移固定资产"""
    conn.rollback()
    with conn.begin():
        try:
            transfer_asset(conn, asset_id, new_user_id, new_department_id, notes, current_user["id"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "资产转移成功"}


@router.post("/{asset_id}/repair")
def do_repair(
    asset_id: int,
    notes: str = Query(default=""),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """送修资产"""
    conn.rollback()
    with conn.begin():
        try:
            repair_asset(conn, asset_id, notes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "资产已送修"}


@router.post("/{asset_id}/repair-done")
def do_repair_done(
    asset_id: int,
    notes: str = Query(default=""),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """修复完成"""
    conn.rollback()
    with conn.begin():
        try:
            repair_done_asset(conn, asset_id, notes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "资产修复完成"}
