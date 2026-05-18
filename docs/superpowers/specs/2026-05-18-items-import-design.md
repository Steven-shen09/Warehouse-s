# 物品批量导入功能 — 设计文档

**日期**: 2026-05-18
**项目**: Warehouse-s
**状态**: 设计中

---

## 概述

在物品管理页面新增批量导入功能，支持通过 CSV 和 Excel 文件批量导入物品数据。

---

## 需求摘要

| 需求 | 决策 |
|------|------|
| 文件格式 | CSV (.csv) + Excel (.xlsx) 均支持 |
| 重复处理策略 | 同名物品默认不勾选；用户勾选后在原有 total_quantity 上累加导入数量 |
| 错误处理策略 | 全部或全不（事务保护，任何错误回滚） |
| 权限控制 | 仅 admin / approver 可操作 |
| UI 设计 | Apple Liquid Glass 设计规范 |

---

## 整体流程

```
选择文件 → 后端解析+验证(/import/preview) → 预览表格(勾选确认) → 后端执行导入(/import/confirm)
```

### 预览表格各行默认状态

| 行类型 | 默认勾选 | 显示 |
|--------|---------|------|
| 有效 + 非重复 | ✅ 勾选 | 正常显示数据 |
| 有效 + 同名重复 | ❌ 不勾选 | 提示"同名物品已存在（ID:N, 现有数量:N），勾选后累加" |
| 无效（字段缺失/格式错误） | ❌ 不勾选 + 禁用 | 红色高亮，显示具体错误原因 |

### 重复行勾选后的行为

- 不创建新物品
- 对已有物品执行 `UPDATE items SET total_quantity = total_quantity + 导入数量`

---

## 导入模板列定义

| 列名 | 必填 | 验证规则 |
|------|------|---------|
| 物品名称 | ✅ | 1-100 字符 |
| 分类 | | 文本 |
| 描述 | | 文本 |
| 存放位置 | | 文本 |
| 总数量 | 默认1 | 整数 ≥1 |
| 单价(元) | 默认0 | 数字 ≥0 |
| 预警阈值 | 默认2 | 整数 ≥0 |

模板下载提供 CSV 和 Excel 两种格式。

---

## API 设计

### POST /api/v1/items/import/preview

接收文件，解析并验证，返回预览数据（不写入数据库）。

- **权限**: admin / approver
- **请求**: multipart/form-data（字段: `file`）
- **响应**:
```json
{
  "rows": [
    {
      "index": 1,
      "data": {"name": "投影仪", "category": "电子设备", ...},
      "status": "ok",
      "message": null,
      "duplicate_item": null
    },
    {
      "index": 2,
      "data": {"name": "笔记本", ...},
      "status": "duplicate",
      "message": "同名物品已存在（ID:3, 现有库存:10）",
      "duplicate_item": {"id": 3, "name": "笔记本", "total_quantity": 10}
    },
    {
      "index": 3,
      "data": {"name": "", ...},
      "status": "error",
      "message": "物品名称不能为空",
      "duplicate_item": null
    }
  ],
  "summary": {"total": 12, "ok": 8, "duplicate": 3, "error": 1}
}
```

### POST /api/v1/items/import/confirm

执行导入，事务内全部或全不。

- **权限**: admin / approver
- **请求**: JSON
```json
{
  "rows": [
    {"index": 1, "action": "create"},
    {"index": 2, "action": "add_to_existing", "item_id": 3},
    {"index": 4, "action": "create"}
  ]
}
```
- **请求同时需要重新上传文件**（multipart/form-data，含 file + selections 字段），后端重新解析后仅处理勾选行
- **响应**:
```json
{
  "message": "成功导入 8 件物品，累加更新 2 件物品",
  "imported": 8,
  "updated": 2,
  "skipped": 1
}
```

### GET /api/v1/items/import/template

下载标准模板文件。

- **权限**: 登录用户
- **查询参数**: `format=csv|xlsx`

---

## 前端 UI

### 按钮位置

筛选栏右侧，与"新增物品"按钮同排，仅 admin/approver 可见。

### 导入模态框 — 三步

**步骤 1 — 选择文件**: 拖拽上传区域、模板下载链接
**步骤 2 — 预览确认**: 数据预览表格（含勾选框）、全选/取消、确认按钮
**步骤 3 — 完成**: 导入结果摘要（成功/累加/跳过数量）、关闭按钮

### 前端 JS 关键函数

| 函数 | 说明 |
|------|------|
| `openImportModal()` | 打开模态框，重置到步骤 1 |
| `handleFileUpload()` | 上传文件到 `/import/preview`，进入步骤 2 |
| `toggleImportRow(index)` | 切换单行勾选 |
| `toggleAllImportRows()` | 全选/全不选 |
| `confirmImport()` | 提交确认数据到 `/import/confirm`，进入步骤 3 |
| `downloadTemplate(format)` | 触发模板下载 |

---

## 后端依赖

- `csv`（Python 标准库）
- `openpyxl`（需安装，用于 Excel 解析）

---

## 涉及文件

| 文件 | 变更 |
|------|------|
| `app/api/items.py` | 新增 3 个端点 |
| `app/schemas/item.py` | 新增 ImportRow schema |
| `frontend/templates/pages/items.html` | 新增导入模态框 + JS 逻辑 |
| `requirements.txt` | 新增 openpyxl 依赖 |

---

## 安全考虑

- 文件大小限制（如 5MB）
- 文件类型白名单（仅 .csv / .xlsx）
- 权限校验（require_role("admin", "approver")）
- SQL 参数化查询（防止 SQL 注入）
- 事务保护（防止部分导入）
