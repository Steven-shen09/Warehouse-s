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
