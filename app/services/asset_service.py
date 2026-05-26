"""固定资产管理服务（领用/交回/转移/报废）"""
from sqlalchemy import text
from app.utils.helpers import generate_disposal_doc_no


def assign_asset(conn, asset_instance_id: int, user_id: int, department_id: int,
                 assignment_date, expected_return_date=None, notes: str = "",
                 created_by: int = None):
    """领用固定资产"""
    asset = conn.execute(text(
        "SELECT ai.*, i.item_type FROM asset_instances ai "
        "JOIN items i ON ai.item_id = i.id WHERE ai.id = :aid"
    ), {"aid": asset_instance_id}).fetchone()
    if not asset:
        raise ValueError("资产实例不存在")
    if asset["status"] != "在库":
        raise ValueError(f"资产当前状态为'{asset['status']}'，无法领用")

    # 更新资产实例
    conn.execute(text(
        "UPDATE asset_instances SET status = '使用中', current_user_id = :uid, "
        "current_department_id = :did, updated_at = NOW() WHERE id = :aid"
    ), {"uid": user_id, "did": department_id, "aid": asset_instance_id})

    # 创建领用记录
    conn.execute(text(
        "INSERT INTO asset_assignments (asset_instance_id, assigned_to_user_id, "
        "assigned_to_department_id, assignment_date, expected_return_date, status, "
        "notes, created_by) "
        "VALUES (:aiid, :auid, :adid, :ad, :erd, '使用中', :nt, :cb)"
    ), {
        "aiid": asset_instance_id, "auid": user_id, "adid": department_id,
        "ad": assignment_date, "erd": expected_return_date,
        "nt": notes, "cb": created_by or user_id,
    })

    # 减少仓库库存
    conn.execute(text(
        "UPDATE warehouse_stocks SET quantity = quantity - 1 "
        "WHERE item_id = :iid AND warehouse_id = :wid AND quantity > 0"
    ), {"iid": asset["item_id"], "wid": asset["warehouse_id"]})


def return_asset(conn, asset_instance_id: int, return_date, notes: str = ""):
    """交回固定资产"""
    asset = conn.execute(text(
        "SELECT * FROM asset_instances WHERE id = :aid"
    ), {"aid": asset_instance_id}).fetchone()
    if not asset:
        raise ValueError("资产实例不存在")
    if asset["status"] != "使用中":
        raise ValueError(f"资产当前状态为'{asset['status']}'，无法交回")

    # 更新活跃的领用记录
    conn.execute(text(
        "UPDATE asset_assignments SET status = '已交回', actual_return_date = :rd, "
        "updated_at = NOW() WHERE asset_instance_id = :aiid AND status = '使用中'"
    ), {"rd": return_date, "aiid": asset_instance_id})

    # 更新资产实例
    conn.execute(text(
        "UPDATE asset_instances SET status = '在库', current_user_id = NULL, "
        "current_department_id = NULL, updated_at = NOW() WHERE id = :aid"
    ), {"aid": asset_instance_id})

    # 恢复仓库库存（INSERT ON CONFLICT 兜底）
    conn.execute(text(
        "INSERT INTO warehouse_stocks (item_id, warehouse_id, quantity) "
        "VALUES (:iid, :wid, 1) "
        "ON CONFLICT (item_id, warehouse_id) DO UPDATE SET quantity = warehouse_stocks.quantity + 1"
    ), {"iid": asset["item_id"], "wid": asset["warehouse_id"]})


def transfer_asset(conn, asset_instance_id: int, new_user_id: int,
                   new_department_id: int, notes: str = "",
                   created_by: int = None):
    """转移固定资产（换人/换部门）"""
    asset = conn.execute(text(
        "SELECT * FROM asset_instances WHERE id = :aid"
    ), {"aid": asset_instance_id}).fetchone()
    if not asset:
        raise ValueError("资产实例不存在")
    if asset["status"] != "使用中":
        raise ValueError(f"资产当前状态为'{asset['status']}'，无法转移")

    # 关闭旧的领用记录
    conn.execute(text(
        "UPDATE asset_assignments SET status = '已交回', actual_return_date = CURRENT_DATE, "
        "updated_at = NOW() WHERE asset_instance_id = :aiid AND status = '使用中'"
    ), {"aiid": asset_instance_id})

    # 更新资产实例
    conn.execute(text(
        "UPDATE asset_instances SET current_user_id = :uid, current_department_id = :did, "
        "updated_at = NOW() WHERE id = :aid"
    ), {"uid": new_user_id, "did": new_department_id, "aid": asset_instance_id})

    # 创建新的领用记录
    conn.execute(text(
        "INSERT INTO asset_assignments (asset_instance_id, assigned_to_user_id, "
        "assigned_to_department_id, assignment_date, status, notes, created_by) "
        "VALUES (:aiid, :auid, :adid, CURRENT_DATE, '使用中', :nt, :cb)"
    ), {
        "aiid": asset_instance_id, "auid": new_user_id,
        "adid": new_department_id, "nt": notes, "cb": created_by or new_user_id,
    })


def repair_asset(conn, asset_instance_id: int, notes: str = ""):
    """送修固定资产"""
    asset = conn.execute(text(
        "SELECT * FROM asset_instances WHERE id = :aid"
    ), {"aid": asset_instance_id}).fetchone()
    if not asset:
        raise ValueError("资产实例不存在")
    if asset["status"] not in ("在库", "使用中"):
        raise ValueError(f"资产当前状态为'{asset['status']}'，无法送修")

    conn.execute(text(
        "UPDATE asset_instances SET status = '维修中', notes = :nt, "
        "updated_at = NOW() WHERE id = :aid"
    ), {"nt": notes, "aid": asset_instance_id})


def repair_done_asset(conn, asset_instance_id: int, notes: str = ""):
    """修复完成"""
    asset = conn.execute(text(
        "SELECT * FROM asset_instances WHERE id = :aid"
    ), {"aid": asset_instance_id}).fetchone()
    if not asset:
        raise ValueError("资产实例不存在")
    if asset["status"] != "维修中":
        raise ValueError(f"资产当前状态为'{asset['status']}'，不在维修中")

    conn.execute(text(
        "UPDATE asset_instances SET status = '在库', notes = :nt, "
        "updated_at = NOW() WHERE id = :aid"
    ), {"nt": notes, "aid": asset_instance_id})


def create_disposal(conn, data: dict, created_by: int) -> dict:
    """创建资产报废申请"""
    asset = conn.execute(text(
        "SELECT * FROM asset_instances WHERE id = :aid"
    ), {"aid": data["asset_instance_id"]}).fetchone()
    if not asset:
        raise ValueError("资产实例不存在")
    if asset["status"] == "已报废":
        raise ValueError("资产已报废，无需重复申请")

    doc_no = generate_disposal_doc_no(conn)
    conn.execute(text(
        "INSERT INTO asset_disposals (document_no, asset_instance_id, disposal_type, "
        "reason, status, residual_value, notes, created_by) "
        "VALUES (:dn, :aiid, :dt, :rs, '待审核', :rv, :nt, :cb)"
    ), {
        "dn": doc_no, "aiid": data["asset_instance_id"],
        "dt": data["disposal_type"], "rs": data.get("reason", ""),
        "rv": data.get("residual_value", 0), "nt": data.get("notes", ""),
        "cb": created_by,
    })
    return {"id": None, "document_no": doc_no}


def approve_disposal(conn, disposal_id: int, approved_by: int):
    """审核通过报废申请"""
    disposal = conn.execute(text(
        "SELECT * FROM asset_disposals WHERE id = :did"
    ), {"did": disposal_id}).fetchone()
    if not disposal:
        raise ValueError("报废单不存在")
    if disposal["status"] != "待审核":
        raise ValueError("只能审核待审核状态的报废单")

    asset = conn.execute(text(
        "SELECT * FROM asset_instances WHERE id = :aid"
    ), {"aid": disposal["asset_instance_id"]}).fetchone()

    # 更新报废单状态
    conn.execute(text(
        "UPDATE asset_disposals SET status = '已通过', approved_by = :ab, "
        "disposal_date = CURRENT_DATE, updated_at = NOW() WHERE id = :did"
    ), {"ab": approved_by, "did": disposal_id})

    # 更新资产实例
    conn.execute(text(
        "UPDATE asset_instances SET status = '已报废', updated_at = NOW() WHERE id = :aid"
    ), {"aid": disposal["asset_instance_id"]})

    # 如果资产在库，减少仓库库存
    if asset and asset["status"] == "在库":
        conn.execute(text(
            "UPDATE warehouse_stocks SET quantity = quantity - 1 "
            "WHERE item_id = :iid AND warehouse_id = :wid AND quantity > 0"
        ), {"iid": asset["item_id"], "wid": asset["warehouse_id"]})
        conn.execute(text(
            "UPDATE items SET total_quantity = total_quantity - 1, updated_at = NOW() WHERE id = :iid"
        ), {"iid": asset["item_id"]})

    # 如果资产在使用中或维修中，关闭领用记录
    if asset and asset["status"] in ("使用中", "维修中"):
        conn.execute(text(
            "UPDATE asset_assignments SET status = '已交回', actual_return_date = CURRENT_DATE, "
            "updated_at = NOW() WHERE asset_instance_id = :aiid AND status = '使用中'"
        ), {"aiid": disposal["asset_instance_id"]})


def reject_disposal(conn, disposal_id: int):
    """驳回报废申请"""
    disposal = conn.execute(text(
        "SELECT * FROM asset_disposals WHERE id = :did"
    ), {"did": disposal_id}).fetchone()
    if not disposal:
        raise ValueError("报废单不存在")
    if disposal["status"] != "待审核":
        raise ValueError("只能驳回待审核状态的报废单")

    conn.execute(text(
        "UPDATE asset_disposals SET status = '已驳回', updated_at = NOW() WHERE id = :did"
    ), {"did": disposal_id})


def request_assign_asset(conn, asset_instance_id: int, user_id: int,
                         department_id: int, expected_return_date=None,
                         notes: str = "", created_by: int = None,
                         user_name: str = "", department_name: str = ""):
    """用户发起固产领用申请（待审核）"""
    asset = conn.execute(text(
        "SELECT * FROM asset_instances WHERE id = :aid"
    ), {"aid": asset_instance_id}).fetchone()
    if not asset:
        raise ValueError("资产实例不存在")
    if asset["status"] != "在库":
        raise ValueError(f"资产当前状态为'{asset['status']}'，无法申请领用")

    from datetime import date as dt_date
    conn.execute(text(
        "INSERT INTO asset_assignments (asset_instance_id, assigned_to_user_id, "
        "assigned_to_department_id, assignment_date, expected_return_date, "
        "status, notes, created_by, user_name, department_name) "
        "VALUES (:aiid, :auid, :adid, :ad, :erd, '待审核', :nt, :cb, :un, :dn)"
    ), {
        "aiid": asset_instance_id, "auid": user_id, "adid": department_id,
        "ad": dt_date.today(), "erd": expected_return_date,
        "nt": notes, "cb": created_by or user_id,
        "un": user_name, "dn": department_name,
    })

    return {"message": "领用申请已提交，等待审核"}


def approve_assignment(conn, assignment_id: int, approved_by: int):
    """审核通过固产领用"""
    assignment = conn.execute(text(
        "SELECT * FROM asset_assignments WHERE id = :aid"
    ), {"aid": assignment_id}).fetchone()
    if not assignment:
        raise ValueError("领用记录不存在")
    if assignment["status"] != "待审核":
        raise ValueError("只能审核待审核状态的领用记录")

    conn.execute(text(
        "UPDATE asset_assignments SET status = '使用中', updated_at = NOW() WHERE id = :aid"
    ), {"aid": assignment_id})

    conn.execute(text(
        "UPDATE asset_instances SET status = '使用中', "
        "current_user_id = :uid, current_department_id = :did, "
        "updated_at = NOW() WHERE id = :aiid"
    ), {
        "uid": assignment["assigned_to_user_id"],
        "did": assignment["assigned_to_department_id"],
        "aiid": assignment["asset_instance_id"],
    })

    # 减少仓库库存
    asset = conn.execute(text(
        "SELECT * FROM asset_instances WHERE id = :aiid"
    ), {"aiid": assignment["asset_instance_id"]}).fetchone()
    conn.execute(text(
        "UPDATE warehouse_stocks SET quantity = quantity - 1 "
        "WHERE item_id = :iid AND warehouse_id = :wid AND quantity > 0"
    ), {"iid": asset["item_id"], "wid": asset["warehouse_id"]})


def reject_assignment(conn, assignment_id: int):
    """驳回固产领用"""
    assignment = conn.execute(text(
        "SELECT * FROM asset_assignments WHERE id = :aid"
    ), {"aid": assignment_id}).fetchone()
    if not assignment:
        raise ValueError("领用记录不存在")
    if assignment["status"] != "待审核":
        raise ValueError("只能驳回待审核状态的领用记录")

    conn.execute(text(
        "UPDATE asset_assignments SET status = '已驳回', updated_at = NOW() WHERE id = :aid"
    ), {"aid": assignment_id})
