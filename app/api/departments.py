"""部门管理路由"""
from sqlalchemy import text
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_db, get_current_user, require_role

router = APIRouter(prefix="/api/v1/departments", tags=["部门管理"])


@router.get("/")
def list_departments(
    keyword: str = "",
    page: int = 1,
    page_size: int = 12,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """部门列表（含子部门扁平展示，分页）"""
    where = "WHERE 1=1"
    params = {}
    if keyword:
        where += " AND name LIKE :kw"
        params["kw"] = f"%{keyword}%"

    total = conn.execute(text(
        f"SELECT COUNT(*) FROM departments d "
        f"LEFT JOIN departments p ON d.parent_id = p.id "
        f"LEFT JOIN users u ON d.manager_id = u.id "
        f"{where}"
    ), params).fetchone()[0]

    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = conn.execute(text(
        f"SELECT d.*, p.name AS parent_name, u.display_name AS manager_name "
        f"FROM departments d "
        f"LEFT JOIN departments p ON d.parent_id = p.id "
        f"LEFT JOIN users u ON d.manager_id = u.id "
        f"{where} ORDER BY d.id LIMIT :limit OFFSET :offset"
    ), params).fetchall()
    return {
        "departments": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/tree")
def department_tree(
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """部门树（层级结构）"""
    rows = conn.execute(text(
        "SELECT * FROM departments ORDER BY parent_id NULLS FIRST, id"
    )).fetchall()
    dep_map = {}
    roots = []
    for r in rows:
        d = dict(r)
        d["children"] = []
        dep_map[d["id"]] = d
    for d in dep_map.values():
        pid = d.get("parent_id")
        if pid and pid in dep_map:
            dep_map[pid]["children"].append(d)
        else:
            roots.append(d)
    return {"departments": roots}


@router.post("/")
def create_department(
    name: str = Query(..., min_length=1, max_length=100),
    parent_id: int = Query(default=None),
    manager_id: int = Query(default=None),
    description: str = Query(default=""),
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """新增部门"""
    conn.rollback()
    with conn.begin():
        result = conn.execute(text(
            "INSERT INTO departments (name, parent_id, manager_id, description) "
            "VALUES (:n, :pid, :mid, :d) RETURNING id"
        ), {"n": name, "pid": parent_id, "mid": manager_id, "d": description})
        did = result.fetchone()[0]
    return {"message": "部门创建成功", "id": did}


@router.put("/{department_id}")
def update_department(
    department_id: int,
    name: str = Query(default=None, max_length=100),
    parent_id: int = Query(default=None),
    manager_id: int = Query(default=None),
    description: str = Query(default=None),
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """更新部门"""
    existing = conn.execute(text("SELECT id FROM departments WHERE id = :did"), {"did": department_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="部门不存在")

    updates = {}
    for field in ["name", "parent_id", "manager_id", "description"]:
        val = locals().get(field)
        if val is not None:
            updates[field] = val

    if updates:
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        params = dict(updates)
        params["did"] = department_id
        conn.rollback()
        with conn.begin():
            conn.execute(text(
                f"UPDATE departments SET {set_clause}, updated_at = NOW() WHERE id = :did"
            ), params)

    return {"message": "部门更新成功"}


@router.delete("/{department_id}")
def delete_department(
    department_id: int,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """删除部门（需无子部门和无关联物品）"""
    existing = conn.execute(text("SELECT id FROM departments WHERE id = :did"), {"did": department_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="部门不存在")

    children = conn.execute(text(
        "SELECT COUNT(*) FROM departments WHERE parent_id = :did"
    ), {"did": department_id}).fetchone()[0]
    if children > 0:
        raise HTTPException(status_code=400, detail="该部门存在子部门，请先删除子部门")

    conn.execute(text("DELETE FROM departments WHERE id = :did"), {"did": department_id})
    conn.commit()
    return {"message": "部门已删除"}
