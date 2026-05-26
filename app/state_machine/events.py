"""状态机事件定义"""

# 租借记录事件
SUBMIT_BORROW = "submit_borrow"          # 提交租借申请
APPROVE = "approve"                      # 审核通过
REJECT = "reject"                        # 审核驳回
RESUBMIT = "resubmit"                    # 驳回后重新提交
RETURN_FULL = "return_full"              # 完全归还
RETURN_PARTIAL = "return_partial"        # 部分归还
AUTO_OVERDUE = "auto_overdue"            # 自动标记逾期

# 物品事件
MARK_DAMAGED = "mark_damaged"            # 标记损坏
MARK_AVAILABLE = "mark_available"        # 修复后恢复可用
UPDATE_STOCK = "update_stock"            # 库存变更（实时计算）

# 消耗品领用事件
SUBMIT_CONSUMABLE = "submit_consumable"          # 提交消耗品领用申请
APPROVE_CONSUMABLE = "approve_consumable"        # 审核通过消耗品领用
REJECT_CONSUMABLE = "reject_consumable"          # 驳回消耗品领用

# 固定资产事件
ASSET_ASSIGN = "asset_assign"                    # 领用资产
ASSET_RETURN = "asset_return"                    # 交回资产
ASSET_REPAIR = "asset_repair"                    # 送修
ASSET_REPAIR_DONE = "asset_repair_done"          # 修复完成
ASSET_DISPOSE = "asset_dispose"                  # 报废资产
ASSET_TRANSFER = "asset_transfer"                # 转移资产（换人/换部门）

# 采购入库事件
PO_APPROVE = "po_approve"                        # 采购入库审核通过
PO_CANCEL = "po_cancel"                          # 取消采购单

# 报废审批事件
DISPOSAL_APPROVE = "disposal_approve"            # 报废审核通过
DISPOSAL_REJECT = "disposal_reject"              # 报废审核驳回
