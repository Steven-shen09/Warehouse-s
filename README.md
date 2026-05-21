# Warehouse-s 物品仓库管理系统

全栈物品仓库管理系统，支持多仓库管理、库存调拨、物品盘点、租借审批、归还追踪、批量导入导出和 RBAC 权限控制。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python FastAPI |
| 数据库 | SQLite（WAL 模式） |
| 前端 | Jinja2 + HTMX 2.0 + Alpine.js 3.14 |
| 样式 | Apple Liquid Glass 设计系统（亮色/暗色模式） |
| 安全 | PBKDF2-SHA256 + JWT (HS256) |

## 快速开始

```bash
pip install -r requirements.txt
python run.py         # http://localhost:8000

python seed_test_data.py   # 可选：插入测试数据
```

### 预置账号

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 全部 |
| 审核员 | approver1 | 123456 | 审核/调拨/盘点 |
| 普通用户 | user1 | 123456 | 查看/租借 |

## 功能模块

### 核心业务
- **多仓库管理** — 仓库 CRUD，物品分仓库存，点击仓库查看存储物品
- **库存调拨** — 批量创建调拨单（同一单据多物品），审核通过后自动转移库存
- **物品盘点** — 创建盘点计划，逐行录入或批量导入实盘数据，差异自动更新库存
- **物品管理** — CRUD、分类/仓库筛选、分仓库存展开、低库存预警
- **租借引擎** — 批量租借、库存检查、事务保护、部分归还
- **审核工作流** — 统一审核工作台（租借+调拨），单条/整单通过驳回，超时检测

### 导入导出
- **物品导入** — CSV/Excel 上传预览确认，同名物品可累加库存
- **物品导出** — CSV/Excel 格式，含分仓库存分布
- **调拨导入** — CSV/Excel 批量导入调拨申请
- **盘点导入** — CSV/Excel 批量录入实盘数据
- 所有导入导出均提供模板下载

### 系统能力
- **RBAC 权限** — admin / approver / user 三级角色
- **操作日志** — 完整审计追踪
- **适配器模式** — 可选 DeepSeek AI 审核、阿里云 OSS/SMS，未配置自动降级
- **状态机** — 严格的记录状态流转

## 项目结构

```
Warehouse-s/
├── run.py / requirements.txt       # 入口和依赖
├── app/
│   ├── api/              # 路由层（11 个模块）
│   ├── services/         # 业务逻辑层（租借/审核/归还/库存/通知）
│   ├── state_machine/    # 状态机引擎
│   ├── schemas/          # Pydantic 模型
│   └── utils/            # 工具函数
├── frontend/
│   ├── templates/        # Jinja2 模板（10 个页面）
│   └── static/           # 本地托管（无外部 CDN）
└── DEV.md                # 详细开发文档
```

## 页面导航

| 页面 | 路径 | 角色 |
|------|------|------|
| 仪表盘 | /dashboard | 全部 |
| 物品管理 | /items | 全部 |
| 仓库管理 | /warehouses | admin/approver |
| 调拨管理 | /transfers | admin/approver |
| 盘点管理 | /inventory-counts | admin/approver |
| 租借记录 | /records | 全部 |
| 审核管理 | /approvals | admin/approver |
| 用户管理 | /users | admin |
| 操作日志 | /logs | admin |

## 文档

- [DEV.md](./DEV.md) — 开发文档（数据库模型、状态机、API 路由、部署说明）
- [warehouse.txt](./warehouse.txt) — 需求方案文档
