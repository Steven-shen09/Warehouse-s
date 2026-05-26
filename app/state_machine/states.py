"""状态定义"""
from enum import Enum


class RecordStatus(str, Enum):
    """租借记录状态"""
    PENDING = "待审核"          # 初始状态：等待审核
    APPROVED = "借出中"         # 审核通过，物品已借出
    REJECTED = "已拒绝"         # 审核驳回
    RETURNED = "已归还"         # 完全归还
    OVERDUE = "逾期"            # 超期未还


class ItemStatus(str, Enum):
    """物品状态"""
    AVAILABLE = "可用"          # 有可借库存
    LENT_OUT = "租借中"         # 全部借出
    DAMAGED = "损坏"            # 管理员标记损坏


class ApprovalAction(str, Enum):
    """审核动作"""
    APPROVED = "approved"
    REJECTED = "rejected"


class ConsumableStatus(str, Enum):
    """消耗品领用状态"""
    PENDING = "待审核"
    PICKED_UP = "已领取"
    REJECTED = "已拒绝"


class AssetStatus(str, Enum):
    """固定资产实例状态"""
    IN_WAREHOUSE = "在库"
    IN_USE = "使用中"
    IN_REPAIR = "维修中"
    DISPOSED = "已报废"


class PurchaseStatus(str, Enum):
    """采购入库状态"""
    PENDING = "待审核"
    INBOUND = "已入库"
    CANCELLED = "已取消"


class DisposalStatus(str, Enum):
    """资产报废审批状态"""
    PENDING = "待审核"
    APPROVED = "已通过"
    REJECTED = "已驳回"
