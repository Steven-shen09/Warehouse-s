"""租借记录路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from app.api.deps import get_db, get_current_user, require_role
from app.schemas.record import BorrowRequest, ReturnRequest, BatchBorrowRequest, DocumentReturnRequest
from app.services.borrow_service import submit_borrow, resubmit_borrow, submit_batch_borrow
from app.services.return_service import process_return, process_return_by_document

router = APIRouter(prefix="/api/v1/records", tags=["租借记录"])


@router.get("/")
def list_records(
    page: int = 1,
    page_size: int = 20,
    status: str = "",
    item_id: int = 0,
    keyword: str = "",
    document_no: str = "",
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """租借记录列表"""
    where = "WHERE 1=1"
    params = {}
    if current_user["role"] == "user":
        where += " AND r.borrower_id = :bid"
        params["bid"] = current_user["id"]
    if status:
        where += " AND r.status = :st"
        params["st"] = status
    if item_id:
        where += " AND r.item_id = :iid"
        params["iid"] = item_id
    if keyword:
        where += " AND (r.borrower_name LIKE :kw1 OR r.reason LIKE :kw2)"
        params["kw1"] = f"%{keyword}%"
        params["kw2"] = f"%{keyword}%"
    if document_no:
        where += " AND r.document_no = :dno"
        params["dno"] = document_no

    total = conn.execute(text(f"SELECT COUNT(*) FROM records r {where}"), params).fetchone()[0]
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    rows = conn.execute(text(
        f"""SELECT r.*, i.name as item_name, i.category as item_category,
                  COALESCE(w.name, '') as source_warehouse_name
           FROM records r JOIN items i ON r.item_id = i.id
           LEFT JOIN warehouses w ON r.source_warehouse_id = w.id
           {where} ORDER BY r.id DESC LIMIT :limit OFFSET :offset"""
    ), params).fetchall()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/batch-borrow")
def create_batch_borrow(
    body: BatchBorrowRequest,
    current_user: dict = Depends(require_role("user")),
    conn=Depends(get_db),
):
    """批量提交租借申请（购物车模式）"""
    try:
        items = [{"item_id": i.item_id, "quantity": i.quantity} for i in body.items]
        result = submit_batch_borrow(
            conn,
            items=items,
            borrower_id=current_user["id"],
            borrower_name=current_user["display_name"] or current_user["username"],
            borrow_date=body.borrow_date,
            expected_return_date=body.expected_return_date,
            reason=body.reason,
            contact=body.contact,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{record_id}")
def get_record(
    record_id: int,
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db),
):
    """获取租借记录详情"""
    row = conn.execute(text(
        """SELECT r.*, i.name as item_name, i.category as item_category
           FROM records r JOIN items i ON r.item_id = i.id WHERE r.id = :rid"""
    ), {"rid": record_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 普通用户只能看自己的
    if current_user["role"] == "user" and row["borrower_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="无权查看此记录")

    return dict(row)


@router.post("/")
def create_borrow(
    body: BorrowRequest,
    current_user: dict = Depends(require_role("user")),
    conn=Depends(get_db),
):
    """提交租借申请"""
    try:
        result = submit_borrow(
            conn,
            item_id=body.item_id,
            borrower_id=current_user["id"],
            borrower_name=current_user["display_name"] or current_user["username"],
            quantity=body.quantity,
            borrow_date=body.borrow_date,
            expected_return_date=body.expected_return_date,
            reason=body.reason,
            contact=body.contact,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{record_id}/resubmit")
def resubmit(
    record_id: int,
    body: BorrowRequest,
    current_user: dict = Depends(require_role("user")),
    conn=Depends(get_db),
):
    """驳回后重新提交申请"""
    try:
        result = resubmit_borrow(
            conn,
            record_id=record_id,
            borrower_id=current_user["id"],
            borrower_name=current_user["display_name"] or current_user["username"],
            quantity=body.quantity,
            borrow_date=body.borrow_date,
            expected_return_date=body.expected_return_date,
            reason=body.reason,
            contact=body.contact,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{record_id}/return")
def return_item(
    record_id: int,
    body: ReturnRequest,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """归还物品"""
    try:
        actual_date = body.actual_return_date or ""
        result = process_return(
            conn,
            record_id=record_id,
            return_quantity=body.return_quantity,
            operator_id=current_user["id"],
            operator_name=current_user["display_name"] or current_user["username"],
            actual_return_date=actual_date,
            return_notes=body.return_notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/by-document/{document_no}/return")
def return_by_document(
    document_no: str,
    body: DocumentReturnRequest,
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """按单据号归还物品"""
    try:
        result = process_return_by_document(
            conn,
            document_no=document_no,
            operator_id=current_user["id"],
            operator_name=current_user["display_name"] or current_user["username"],
            actual_return_date=body.actual_return_date,
            return_notes=body.return_notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
