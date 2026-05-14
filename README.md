# Warehouse-s 物品租借管理系统

全栈物品租借管理系统，支持物品管理、租借审批工作流、归还追踪、RBAC 权限控制和完整操作日志。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python FastAPI |
| 数据库 | SQLite（WAL 模式） |
| 前端 | Jinja2 + HTMX 2.0 + Alpine.js 3.14 |
| 样式 | Flat Design 自定义设计系统（支持暗色模式） |
| 安全 | PBKDF2-SHA256 + JWT (HS256) |

## 快速开始

```bash
pip install -r requirements.txt
python run.py
```

访问 http://localhost:8000 即可使用。

### 预置账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 审核员 | approver1 | 123456 |
| 普通用户 | user1 | 123456 |

## 功能模块

- **物品管理** — 物品 CRUD、分类筛选、库存实时计算、低库存预警
- **租借引擎** — 库存检查、事务保护、部分归还支持
- **审核工作流** — 单级审核、超时检测、驳回后重新提交
- **状态机** — 严格的记录状态流转：待审核 → 借出中 → 已归还/逾期
- **RBAC 权限** — admin / approver / user 三级角色
- **操作日志** — 完整审计追踪
- **适配器模式** — 可选 AI 审核（DeepSeek）、OSS 图片存储（阿里云）、SMS 通知（阿里云），未配置自动降级

## 项目结构

```
Warehouse-s/
├── run.py                         # 应用入口
├── app/
│   ├── api/                       # 路由层（auth/items/records/approvals 等）
│   ├── services/                  # 业务逻辑层（租借/审核/归还/库存/通知）
│   ├── state_machine/             # 状态机引擎
│   ├── schemas/                   # Pydantic 模型
│   ├── adapters/                  # 第三方服务适配层
│   └── utils/                     # 工具函数（安全/日期）
├── frontend/
│   ├── templates/                 # Jinja2 模板
│   └── static/                    # 本地托管静态资源（无外部 CDN 依赖）
└── DEV.md                         # 开发文档
```

## 文档

- [DEV.md](./DEV.md) — 详细开发文档（数据库模型、状态机、API 路由）
- [warehouse.txt](./warehouse.txt) — 需求方案文档
