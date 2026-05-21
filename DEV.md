# Warehouse-s 物品租借系统 — 开发文档

## 一、项目概述

物品仓库管理系统，支持多仓库物品全生命周期管理、库存调拨、物品盘点、租借审批工作流、归还追踪、批量导入导出。后端 Python FastAPI + SQLite（WAL 模式），前端 Jinja2 + HTMX + Alpine.js，Apple Liquid Glass 设计系统。

## 二、快速开始

### 环境要求

- Python 3.10+
- pip

### 安装与启动

```bash
cd Warehouse-s
pip install -r requirements.txt
python run.py
```

- 前端界面：http://localhost:8000
- 局域网访问（移动端测试）：http://<本机IP>:8000
- Swagger API 文档：http://localhost:8000/docs
- 首次启动自动创建数据库并写入种子数据

### 预置账号

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 全部权限 |
| 审核员 | approver1 | 123456 | 物品管理、审核、调拨、盘点、归还 |
| 普通用户 | user1 | 123456 | 物品查看、提交租借申请 |

### 环境变量（`.env`）

```
SECRET_KEY=warehouse-s-dev-secret-key-change-in-production
DATABASE_PATH=data/warehouse.db
APPROVAL_TIMEOUT_HOURS=24         # 审核超时小时数

# 可选：DeepSeek AI 智能审核
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 可选：阿里云 OSS 图片存储
OSS_ACCESS_KEY_ID=
OSS_ACCESS_KEY_SECRET=
OSS_BUCKET_NAME=
OSS_ENDPOINT=

# 可选：阿里云 SMS 短信通知
SMS_ACCESS_KEY_ID=
SMS_ACCESS_KEY_SECRET=
SMS_SIGN_NAME=
SMS_TEMPLATE_CODE=
```

不配置外部服务时，系统自动使用空适配器降级，不影响核心功能。

所有前端资源（CSS/JS/字体）均已本地托管，**无需任何外部 CDN 连接**即可运行。

### 测试数据

```bash
python seed_test_data.py    # 插入 4 仓库 / 27 物品 / 4 调拨 / 1 盘点
```

---

## 三、项目结构

```
Warehouse-s/
├── run.py                         # 应用入口
├── requirements.txt               # Python 依赖（含 openpyxl）
├── seed_test_data.py              # 测试数据脚本
├── .env                           # 环境变量
├── CLAUDE.md                      # Claude Code 指引
├── DEV.md                         # 本开发文档
│
├── app/                           # ── 应用主包 ──
│   ├── __init__.py                # FastAPI 工厂函数 create_app()
│   ├── config.py                  # 配置管理（Settings 类）
│   ├── database.py                # SQLite 连接、建表、种子数据
│   │
│   ├── api/                       # ── 路由层 ──
│   │   ├── __init__.py            # 路由注册
│   │   ├── deps.py                # 依赖注入（get_db, get_current_user, require_role）
│   │   ├── auth.py                # /api/v1/auth/*
│   │   ├── users.py               # /api/v1/users/*
│   │   ├── items.py               # /api/v1/items/*（含导入导出）
│   │   ├── records.py             # /api/v1/records/*
│   │   ├── approvals.py           # /api/v1/approvals/*（租借+调拨审核）
│   │   ├── warehouses.py          # /api/v1/warehouses/*
│   │   ├── transfers.py           # /api/v1/transfers/*（含批量创建）
│   │   ├── inventory_counts.py    # /api/v1/inventory-counts/*
│   │   ├── stats.py               # /api/v1/stats
│   │   ├── audit_logs.py          # /api/v1/logs
│   │   └── frontend.py            # 前端页面路由
│   │
│   ├── services/                  # ── 业务逻辑层 ──
│   │   ├── borrow_service.py      # 租借引擎
│   │   ├── approval_service.py    # 审核工作流
│   │   ├── return_service.py      # 归还引擎
│   │   ├── inventory_service.py   # 库存服务（分仓计算）
│   │   ├── notification_service.py# 通知服务
│   │   └── audit_service.py       # 审计服务
│   │
│   ├── state_machine/             # ── 状态机引擎 ──
│   │   ├── states.py              # 状态枚举
│   │   ├── transitions.py         # 合法转换表
│   │   └── events.py              # 事件常量
│   │
│   ├── schemas/                   # ── Pydantic Schema ──
│   │   ├── auth.py                # 登录/修改密码
│   │   ├── user.py                # 用户 CRUD
│   │   ├── item.py                # 物品 CRUD + 导入导出
│   │   ├── warehouse.py           # 仓库/调拨/盘点
│   │   ├── record.py              # 租借申请/归还
│   │   ├── approval.py            # 审核操作
│   │   └── common.py              # 通用
│   │
│   ├── adapters/                  # ── 第三方服务适配层 ──
│   ├── middleware/                # ── 中间件（预留）──
│   └── utils/                     # ── 工具函数 ──
│       ├── security.py            # 密码哈希 + JWT
│       └── helpers.py             # 日期处理等
│
├── frontend/                      # ── 前端资源 ──
│   ├── templates/
│   │   ├── base.html              # 基础布局 + 侧边栏导航
│   │   ├── login.html             # 登录页
│   │   ├── dashboard.html         # 仪表盘
│   │   └── pages/
│   │       ├── items.html         # 物品管理（CRUD/导入/导出/分仓展开）
│   │       ├── records.html       # 租借记录（申请/归还/分组）
│   │       ├── approvals.html     # 审核管理（租借+调拨统一审核）
│   │       ├── warehouses.html    # 仓库管理（CRUD/物品查看）
│   │       ├── transfers.html     # 调拨管理（批量创建/导入/分组）
│   │       ├── inventory_counts.html # 盘点管理（创建/录入/导入）
│   │       ├── users.html         # 用户管理
│   │       └── logs.html          # 操作日志
│   └── static/
│       ├── css/
│       │   ├── style.css          # Apple Liquid Glass 设计系统
│       │   ├── bootstrap-icons.css
│       │   └── fonts/
│       └── js/
│           ├── app.js             # 全局状态 + API 封装
│           ├── htmx.min.js
│           └── alpine.min.js
│
├── data/                          # SQLite 数据库文件
└── docs/superpowers/              # 设计文档和计划
    ├── specs/                     # 功能设计 spec
    └── plans/                     # 实施计划
```

---

## 四、数据库模型

### 核心表（11 张）

#### users — 用户表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| username | TEXT UNIQUE | |
| password_hash | TEXT | PBKDF2-SHA256 |
| display_name | TEXT | |
| role | TEXT CHECK(admin/approver/user) | |
| is_active | INTEGER | 1=启用 |
| created_at / updated_at | TEXT | |

#### items — 物品表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| name | TEXT | |
| category | TEXT | |
| description | TEXT | |
| location | TEXT | 旧字段，已废弃（由 warehouse_stocks 取代） |
| total_quantity | INTEGER | = 所有仓库库存之和 |
| status | TEXT CHECK(可用/租借中/损坏) | 实时计算 |
| value | REAL | 单价 |
| low_stock_threshold | INTEGER | |
| created_at / updated_at | TEXT | |

#### warehouses — 仓库表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| name | TEXT | 仓库名称 |
| location | TEXT | 仓库地址 |
| description | TEXT | |
| created_at / updated_at | TEXT | |

#### warehouse_stocks — 分仓库存表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| item_id | INTEGER FK→items | |
| warehouse_id | INTEGER FK→warehouses | |
| quantity | INTEGER | |
| UNIQUE(item_id, warehouse_id) | | |

#### transfers — 调拨记录表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| item_id | INTEGER FK→items | |
| from_warehouse_id | INTEGER FK→warehouses | |
| to_warehouse_id | INTEGER FK→warehouses | |
| quantity | INTEGER | |
| reason | TEXT | |
| status | TEXT CHECK(待审核/已通过/已驳回) | |
| document_no | TEXT | 单号 DB-YYYYMMDD-XXX |
| created_by | INTEGER FK→users | |
| approved_by | INTEGER FK→users | |
| created_at / updated_at | TEXT | |

#### inventory_counts — 盘点记录表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| warehouse_id | INTEGER FK→warehouses | |
| name | TEXT | |
| status | TEXT CHECK(进行中/已完成/已确认) | |
| created_by | INTEGER FK→users | |
| completed_at | TEXT | |
| created_at / updated_at | TEXT | |

#### inventory_count_items — 盘点明细表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| count_id | INTEGER FK→inventory_counts | |
| item_id | INTEGER FK→items | |
| expected_quantity | INTEGER | 系统库存 |
| actual_quantity | INTEGER | 实盘数量 |
| difference | INTEGER | actual - expected |
| notes | TEXT | |
| counted_at | TEXT | |

#### records — 租借记录表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| item_id | INTEGER FK→items | |
| borrower_id | INTEGER FK→users | |
| document_no | TEXT | 单号 DJ-YYYYMMDD-XXXX |
| quantity | INTEGER | |
| borrow_date / expected_return_date / actual_return_date | TEXT | |
| status | TEXT CHECK(待审核/借出中/已拒绝/已归还/逾期) | |
| reason / return_notes | TEXT | |
| approval_deadline | TEXT | |
| original_record_id | INTEGER FK→records | 部分归还追溯 |

#### approvals — 审核记录表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| record_id | INTEGER FK→records | |
| approver_id | INTEGER FK→users | |
| action | TEXT CHECK(approved/rejected) | |
| comment / ai_suggestion | TEXT | |

#### audit_logs — 操作日志表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| user_id | INTEGER FK→users | |
| action / target_type / target_id / detail | TEXT/INTEGER/TEXT | |
| created_at | TEXT | |

---

## 五、状态机

### 租借记录状态流转

```
                 ┌──────────┐
 提交申请         │  待审核   │
 ───────────────► │          │
                 └────┬─────┘
                      │
           ┌──────────┼──────────┐
           │          │          │
      审核通过    超时提醒    审核驳回
           │                    │
           ▼                    ▼
      ┌─────────┐         ┌──────────┐
      │  借出中   │         │  已拒绝   │
      └────┬────┘         └──────────┘
           │
  ┌────────┼────────┐
  │        │        │
完全归还 部分归还   超期
  │        │    (自动检测)
  ▼        ▼        ▼
┌────────┐ ┌───────┐ ┌──────┐
│ 已归还  │ │借出中  │ │ 逾期  │
└────────┘ │(部分)  │ └──────┘
           └───────┘
```

### 调拨状态流转

```
创建 → 待审核 ──通过→ 已通过（执行库存转移）
            └──驳回→ 已驳回
```

---

## 六、API 路由

### 认证 `/api/v1/auth`
| 方法 | 路径 | 权限 |
|------|------|------|
| POST | /login | 公开 |
| GET | /me | 登录 |
| PUT | /change-password | 登录 |

### 用户管理 `/api/v1/users`
| 方法 | 路径 | 权限 |
|------|------|------|
| GET | / | admin |
| POST | / | admin |
| GET | /{id} | admin |
| PUT | /{id} | admin |
| PUT | /{id}/toggle | admin |
| PUT | /{id}/reset-password | admin |

### 物品管理 `/api/v1/items`
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | / | 列表（搜索/分类/状态/仓库筛选/分页） | 登录 |
| GET | /categories | 分类列表 | 登录 |
| GET | /export | 导出 CSV/Excel（含仓库库存列） | admin/approver |
| GET | /{id} | 详情 | 登录 |
| POST | / | 新增（自动分配仓库） | admin/approver |
| PUT | /{id} | 更新 | admin/approver |
| DELETE | /{id} | 删除 | admin |
| PUT | /{id}/mark-damaged | 标记损坏 | admin/approver |
| PUT | /{id}/mark-available | 恢复可用 | admin/approver |
| POST | /import/preview | 导入预览 | admin/approver |
| POST | /import/confirm | 导入确认 | admin/approver |
| GET | /import/template | 导入模板下载 | 登录 |

### 仓库管理 `/api/v1/warehouses`
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | / | 列表 | 登录 |
| POST | / | 新增 | admin |
| PUT | /{id} | 编辑 | admin |
| DELETE | /{id} | 删除 | admin |
| GET | /{id}/items | 仓库内物品列表 | 登录 |

### 调拨管理 `/api/v1/transfers`
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | / | 列表 | 登录 |
| POST | / | 单条创建 | admin/approver |
| POST | /batch | 批量创建（同一单据号） | admin/approver |
| PUT | /{id}/approve | 审核通过 | admin/approver |
| PUT | /{id}/reject | 驳回 | admin/approver |
| PUT | /by-document/{docNo}/approve | 整单通过 | admin/approver |
| PUT | /by-document/{docNo}/reject | 整单驳回 | admin/approver |
| POST | /import/preview | 导入预览 | admin/approver |
| POST | /import/confirm | 导入确认 | admin/approver |
| GET | /import/template | 导入模板 | 登录 |

### 盘点管理 `/api/v1/inventory-counts`
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | / | 列表 | 登录 |
| POST | / | 创建 | admin/approver |
| GET | /{id} | 详情 | 登录 |
| DELETE | /{id} | 删除（无数据时） | admin/approver |
| PUT | /{id}/items/{item_id} | 录入实盘 | admin/approver |
| PUT | /{id}/complete | 完成盘点 | admin/approver |
| PUT | /{id}/confirm | 确认差异→更新库存 | admin |
| POST | /{id}/import/preview | 导入实盘预览 | admin/approver |
| POST | /{id}/import/confirm | 导入实盘确认 | admin/approver |
| GET | /import/template | 导入模板 | 登录 |

### 审核管理 `/api/v1/approvals`
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | /pending-grouped | 租借待审（分组） | admin/approver |
| GET | /pending-transfers | 调拨待审（分组） | admin/approver |
| GET | /stats | 统计数据（含调拨/待归还） | admin/approver |
| PUT | /{id}/approve | 租借通过 | admin/approver |
| PUT | /{id}/reject | 租借驳回 | admin/approver |
| PUT | /by-document/{docNo}/approve | 整单通过 | admin/approver |
| PUT | /by-document/{docNo}/reject | 整单驳回 | admin/approver |

### 租借记录 `/api/v1/records`
| 方法 | 路径 | 权限 |
|------|------|------|
| GET | / | 登录 |
| POST | / | user |
| POST | /batch-borrow | user |
| PUT | /{id}/return | admin/approver |
| PUT | /by-document/{docNo}/return | admin/approver |

### 前端页面路由

| 路径 | 页面 | 权限 |
|------|------|------|
| /login | 登录 | 公开 |
| /dashboard | 仪表盘 | 登录 |
| /items | 物品管理 | 登录 |
| /warehouses | 仓库管理 | admin/approver |
| /transfers | 调拨管理 | admin/approver |
| /inventory-counts | 盘点管理 | admin/approver |
| /records | 租借记录 | 登录 |
| /approvals | 审核管理 | admin/approver |
| /users | 用户管理 | admin |
| /logs | 操作日志 | admin |

---

## 七、核心功能说明

### 多仓库体系
- items.total_quantity = SUM(warehouse_stocks.quantity)
- 新建物品自动分配到默认仓库
- 仓库筛选替代旧的位置筛选
- 物品列表点击行可展开各仓库库存明细

### 库存调拨
- 支持单条和批量（同一单据号多物品）
- 创建时校验源仓库库存
- 通过后事务内扣减+增加，失败回滚
- 调拨列表按单据号分组展示（doc-group 模式）
- 状态映射：数据库中文(待审核/已通过/已驳回) ↔ API英文(pending/approved/rejected)

### 物品盘点
- 创建盘点→自动生成该仓库所有物品明细
- 支持逐行录入或 CSV 导入实盘数据
- 差异自动计算（actual - expected）
- 确认后更新 warehouse_stocks

### 物品导入导出
- 导入：CSV/Excel 上传→预览→确认，三步流程
- 导出：CSV/Excel 格式，含仓库库存分布列
- 导入列：名称/分类/描述/存放仓库/总库存/单价/预警阈值
- 同名物品可累加到已有库存

### 审核工作台
- 统一待办：租借审批 + 调拨审批
- 类型筛选切换，支持单条和整单操作
- 统计卡片：租借待审/调拨待审/待归还/超时/今日处理
- 待归还卡片可点击跳转租借记录

### 权限控制
- admin：全部权限
- approver：物品管理/审核/调拨创建/盘点操作
- user：物品查看/租借申请

---

## 八、前端技术栈

| 技术 | 用途 |
|------|------|
| Jinja2 | 模板渲染 |
| HTMX 2.0 | 无刷新交互 |
| Alpine.js 3.14 | 客户端状态 |
| Bootstrap Icons 1.11 | 图标 |
| Apple Liquid Glass CSS | 设计系统（玻璃态/暗色模式） |

前端全局对象 `AppState` 管理认证和主题，`api()` 封装带 JWT 的 fetch 请求。

---

## 九、关键设计说明

### 库存一致性
所有库存变更使用 `BEGIN IMMEDIATE` 事务保护。

### 状态机集成
业务层禁止直接修改 status，必须通过 state_machine 引擎。

### RBAC 权限
FastAPI `Depends(require_role("admin", "approver"))` 依赖注入。

### 第三方适配器
外部服务未配置时 NullAdapter 降级。

### 安全
- PBKDF2-SHA256 密码哈希（10 万次迭代）
- JWT HS256 签名，24h 过期
- 所有 SQL 参数化查询，防注入
- 前端 escapeHtml() 防 XSS
- 文件上传白名单(.csv/.xlsx) + 大小限制(5MB)

---

## 十、部署

### 开发
```bash
python run.py          # 127.0.0.1:8000
```

### 局域网（移动端测试）
```bash
python run.py          # 0.0.0.0:8000，http://<本机IP>:8000
```

### 生产
```bash
uvicorn run:app --host 0.0.0.0 --port 8000 --workers 4
```
