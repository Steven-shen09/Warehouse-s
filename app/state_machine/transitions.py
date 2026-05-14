"""状态转换表：定义所有合法状态转换及校验"""
from app.state_machine.states import RecordStatus
from app.state_machine.events import (
    SUBMIT_BORROW, APPROVE, REJECT, RESUBMIT,
    RETURN_FULL, RETURN_PARTIAL, AUTO_OVERDUE,
    MARK_DAMAGED, MARK_AVAILABLE,
)

# ── 租借记录状态转换表 ──
# 格式：{ (当前状态, 事件) : 目标状态 }
RECORD_TRANSITIONS = {
    # 初始 → 提交申请 → 待审核
    ("__initial__", SUBMIT_BORROW): RecordStatus.PENDING,
    # 待审核 → 通过 → 借出中
    (RecordStatus.PENDING, APPROVE): RecordStatus.APPROVED,
    # 待审核 → 驳回 → 已拒绝
    (RecordStatus.PENDING, REJECT): RecordStatus.REJECTED,
    # 已拒绝 → 重新提交 → 待审核
    (RecordStatus.REJECTED, RESUBMIT): RecordStatus.PENDING,
    # 借出中 → 完全归还 → 已归还
    (RecordStatus.APPROVED, RETURN_FULL): RecordStatus.RETURNED,
    # 借出中 → 部分归还 → 借出中（剩余数量 > 0）
    (RecordStatus.APPROVED, RETURN_PARTIAL): RecordStatus.APPROVED,
    # 借出中 → 超时标记 → 逾期
    (RecordStatus.APPROVED, AUTO_OVERDUE): RecordStatus.OVERDUE,
    # 逾期 → 完全归还 → 已归还
    (RecordStatus.OVERDUE, RETURN_FULL): RecordStatus.RETURNED,
    # 逾期 → 部分归还 → 逾期（仍需跟踪剩余数量）
    (RecordStatus.OVERDUE, RETURN_PARTIAL): RecordStatus.OVERDUE,
}


def can_transition(current_status: str, event: str) -> bool:
    """检查从当前状态是否可以执行指定事件"""
    lookup = current_status if current_status != "__initial__" else "__initial__"
    return (RecordStatus(lookup), event) in RECORD_TRANSITIONS


def transition(current_status: str, event: str) -> str:
    """执行状态转换，返回目标状态；非法转换抛出 ValueError"""
    lookup = RecordStatus(current_status)
    key = (lookup, event)
    if key not in RECORD_TRANSITIONS:
        raise ValueError(f"非法状态转换：{current_status} --({event})--> ?")
    target = RECORD_TRANSITIONS[key]
    return target.value


# ── 物品状态转换 ──
# 物品状态由 inventory_service 实时计算，以下是手动允许的转换
ITEM_TRANSITIONS = {
    # 可用 → 标记损坏
    ("可用", MARK_DAMAGED): "损坏",
    # 损坏 → 修复
    ("损坏", MARK_AVAILABLE): "可用",
    # 租借中 → 标记损坏
    ("租借中", MARK_DAMAGED): "损坏",
}


def can_transition_item(current_status: str, event: str) -> bool:
    """检查物品状态转换是否合法"""
    return (current_status, event) in ITEM_TRANSITIONS
