"""状态转换表：定义所有合法状态转换及校验"""
from app.state_machine.states import RecordStatus, ConsumableStatus, AssetStatus, PurchaseStatus, DisposalStatus
from app.state_machine.events import (
    SUBMIT_BORROW, APPROVE, REJECT, RESUBMIT,
    RETURN_FULL, RETURN_PARTIAL, AUTO_OVERDUE,
    MARK_DAMAGED, MARK_AVAILABLE,
    SUBMIT_CONSUMABLE, APPROVE_CONSUMABLE, REJECT_CONSUMABLE,
    ASSET_ASSIGN, ASSET_RETURN, ASSET_REPAIR, ASSET_REPAIR_DONE,
    ASSET_DISPOSE, ASSET_TRANSFER,
    PO_APPROVE, PO_CANCEL,
    DISPOSAL_APPROVE, DISPOSAL_REJECT,
)

# ── 租借记录状态转换表 ──
RECORD_TRANSITIONS = {
    ("__initial__", SUBMIT_BORROW): RecordStatus.PENDING,
    (RecordStatus.PENDING, APPROVE): RecordStatus.APPROVED,
    (RecordStatus.PENDING, REJECT): RecordStatus.REJECTED,
    (RecordStatus.REJECTED, RESUBMIT): RecordStatus.PENDING,
    (RecordStatus.APPROVED, RETURN_FULL): RecordStatus.RETURNED,
    (RecordStatus.APPROVED, RETURN_PARTIAL): RecordStatus.APPROVED,
    (RecordStatus.APPROVED, AUTO_OVERDUE): RecordStatus.OVERDUE,
    (RecordStatus.OVERDUE, RETURN_FULL): RecordStatus.RETURNED,
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
ITEM_TRANSITIONS = {
    ("可用", MARK_DAMAGED): "损坏",
    ("损坏", MARK_AVAILABLE): "可用",
    ("租借中", MARK_DAMAGED): "损坏",
}


def can_transition_item(current_status: str, event: str) -> bool:
    """检查物品状态转换是否合法"""
    return (current_status, event) in ITEM_TRANSITIONS


# ── 消耗品领用状态转换 ──
CONSUMABLE_TRANSITIONS = {
    ("__initial__", SUBMIT_CONSUMABLE): ConsumableStatus.PENDING,
    (ConsumableStatus.PENDING, APPROVE_CONSUMABLE): ConsumableStatus.PICKED_UP,
    (ConsumableStatus.PENDING, REJECT_CONSUMABLE): ConsumableStatus.REJECTED,
}


def can_transition_consumable(current_status: str, event: str) -> bool:
    lookup = ConsumableStatus(current_status) if current_status != "__initial__" else "__initial__"
    key = (lookup, event) if isinstance(lookup, ConsumableStatus) else ("__initial__", event)
    return key in CONSUMABLE_TRANSITIONS


def transition_consumable(current_status: str, event: str) -> str:
    lookup = ConsumableStatus(current_status) if current_status != "__initial__" else None
    if lookup is None:
        key = ("__initial__", event)
    else:
        key = (lookup, event)
    if key not in CONSUMABLE_TRANSITIONS:
        raise ValueError(f"非法状态转换：{current_status} --({event})--> ?")
    return CONSUMABLE_TRANSITIONS[key].value


# ── 固定资产实例状态转换 ──
ASSET_TRANSITIONS_TABLE = {
    ("__initial__", None): AssetStatus.IN_WAREHOUSE,
    (AssetStatus.IN_WAREHOUSE, ASSET_ASSIGN): AssetStatus.IN_USE,
    (AssetStatus.IN_USE, ASSET_RETURN): AssetStatus.IN_WAREHOUSE,
    (AssetStatus.IN_WAREHOUSE, ASSET_REPAIR): AssetStatus.IN_REPAIR,
    (AssetStatus.IN_USE, ASSET_REPAIR): AssetStatus.IN_REPAIR,
    (AssetStatus.IN_REPAIR, ASSET_REPAIR_DONE): AssetStatus.IN_WAREHOUSE,
    (AssetStatus.IN_WAREHOUSE, ASSET_DISPOSE): AssetStatus.DISPOSED,
    (AssetStatus.IN_REPAIR, ASSET_DISPOSE): AssetStatus.DISPOSED,
    (AssetStatus.IN_USE, ASSET_TRANSFER): AssetStatus.IN_USE,
    (AssetStatus.IN_WAREHOUSE, ASSET_TRANSFER): AssetStatus.IN_USE,
}


def can_transition_asset(current_status: str, event: str) -> bool:
    lookup = AssetStatus(current_status) if current_status != "__initial__" else None
    if lookup is None:
        key = ("__initial__", event)
    else:
        key = (lookup, event)
    return key in ASSET_TRANSITIONS_TABLE


def transition_asset(current_status: str, event: str) -> str:
    lookup = AssetStatus(current_status) if current_status != "__initial__" else None
    if lookup is None:
        key = ("__initial__", event)
    else:
        key = (lookup, event)
    if key not in ASSET_TRANSITIONS_TABLE:
        raise ValueError(f"非法资产状态转换：{current_status} --({event})--> ?")
    return ASSET_TRANSITIONS_TABLE[key].value


# ── 采购入库状态转换 ──
PURCHASE_TRANSITIONS = {
    ("__initial__", None): PurchaseStatus.PENDING,
    (PurchaseStatus.PENDING, PO_APPROVE): PurchaseStatus.INBOUND,
    (PurchaseStatus.PENDING, PO_CANCEL): PurchaseStatus.CANCELLED,
}


def can_transition_purchase(current_status: str, event: str) -> bool:
    lookup = PurchaseStatus(current_status) if current_status != "__initial__" else None
    if lookup is None:
        key = ("__initial__", event)
    else:
        key = (lookup, event)
    return key in PURCHASE_TRANSITIONS


def transition_purchase(current_status: str, event: str) -> str:
    lookup = PurchaseStatus(current_status) if current_status != "__initial__" else None
    if lookup is None:
        key = ("__initial__", event)
    else:
        key = (lookup, event)
    if key not in PURCHASE_TRANSITIONS:
        raise ValueError(f"非法采购状态转换：{current_status} --({event})--> ?")
    return PURCHASE_TRANSITIONS[key].value


# ── 报废审批状态转换 ──
DISPOSAL_TRANSITIONS = {
    ("__initial__", None): DisposalStatus.PENDING,
    (DisposalStatus.PENDING, DISPOSAL_APPROVE): DisposalStatus.APPROVED,
    (DisposalStatus.PENDING, DISPOSAL_REJECT): DisposalStatus.REJECTED,
}


def can_transition_disposal(current_status: str, event: str) -> bool:
    lookup = DisposalStatus(current_status) if current_status != "__initial__" else None
    if lookup is None:
        key = ("__initial__", event)
    else:
        key = (lookup, event)
    return key in DISPOSAL_TRANSITIONS


def transition_disposal(current_status: str, event: str) -> str:
    lookup = DisposalStatus(current_status) if current_status != "__initial__" else None
    if lookup is None:
        key = ("__initial__", event)
    else:
        key = (lookup, event)
    if key not in DISPOSAL_TRANSITIONS:
        raise ValueError(f"非法报废状态转换：{current_status} --({event})--> ?")
    return DISPOSAL_TRANSITIONS[key].value
