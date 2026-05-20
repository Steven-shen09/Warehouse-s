# Warehouse-s 物品租借系统 — 开发文档

## 一、项目概述

物品租借管理系统，支持物品全生命周期管理、租借审批工作流、归还追踪。后端 Python FastAPI + SQLite，前端 Jinja2 + HTMX + Alpine.js。

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
- Swagger API 文档：http://localhost:8000/docs
- 首次启动自动创建数据库并写入种子数据

### 预置账号

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 全部权限 |
| 审核员 | approver1 | 123456 | 物品管理、审核、归还 |
| 普通用户 | user1 | 123456 | 物品查看、提交申请 |

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

所有前端资源（CSS/JS/字体）均已本地托管，**无需任何外部 CDN 连接**即可运行，页面均为秒开。

---

## 三、项目结构

```
Warehouse-s/
├── run.py                         # 应用入口
├── requirements.txt               # Python 依赖
├── .env                           # 环境变量
├── .gitignore
├── CLAUDE.md                      # Claude Code 指引
├── warehouse.txt                  # 需求方案文档
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
│   │   ├── items.py               # /api/v1/items/*
│   │   ├── records.py             # /api/v1/records/*
│   │   ├── approvals.py           # /api/v1/approvals/*
│   │   ├── stats.py               # /api/v1/stats
│   │   ├── audit_logs.py          # /api/v1/logs
│   │   └── frontend.py            # 前端页面路由（/dashboard, /items 等）
│   │
│   ├── services/                  # ── 业务逻辑层 ──
│   │   ├── borrow_service.py      # 租借引擎：库存检查 + 申请提交
│   │   ├── approval_service.py    # 审核工作流：通过/驳回/超时检测
│   │   ├── return_service.py      # 归还引擎：完全/部分归还
│   │   ├── inventory_service.py   # 库存服务：实时计算 + 事务保护
│   │   ├── notification_service.py# 通知服务：审核/归还提醒 + 超时检测
│   │   └── audit_service.py       # 审计服务：操作日志记录
│   │
│   ├── state_machine/             # ── 状态机引擎 ──
│   │   ├── states.py              # 状态枚举
│   │   ├── transitions.py         # 合法转换表 + can_transition() / transition()
│   │   └── events.py              # 事件常量
│   │
│   ├── schemas/                   # ── Pydantic Schema ──
│   │   ├── auth.py                # 登录/修改密码
│   │   ├── user.py                # 用户 CRUD
│   │   ├── item.py                # 物品 CRUD
│   │   ├── record.py              # 租借申请/归还
│   │   ├── approval.py            # 审核操作
│   │   └── common.py              # 通用（分页、消息）
│   │
│   ├── adapters/                  # ── 第三方服务适配层 ──
│   │   ├── base.py                # AI/OSS/SMS 抽象基类
│   │   ├── ai_adapter.py          # DeepSeek AI 适配器
│   │   ├── oss_adapter.py         # 阿里云 OSS 适配器
│   │   ├── sms_adapter.py         # 阿里云 SMS 适配器
│   │   └── null_adapter.py        # 空适配器（无外部服务时降级）
│   │
│   ├── middleware/                # ── 中间件（预留）──
│   └── utils/                     # ── 工具函数 ──
│       ├── security.py            # 密码哈希（PBKDF2-SHA256）+ JWT
│       └── helpers.py             # 日期处理等
│
├── frontend/                      # ── 前端资源 ──
│   ├── templates/
│   │   ├── base.html              # 基础布局 + 导航栏 + 侧边栏
│   │   ├── login.html             # 登录页
│   │   ├── dashboard.html         # 仪表盘（统计卡片 + 最近记录）
│   │   └── pages/
│   │       ├── items.html         # 物品管理（CRUD + 搜索/筛选/分页）
│   │       ├── records.html       # 租借记录（申请/归还）
│   │       ├── approvals.html     # 审核管理（通过/驳回/超时标记）
│   │       ├── users.html         # 用户管理（CRUD/启停/重置密码）
│   │       └── logs.html          # 操作日志
│   └── static/
│       ├── css/
│       │   ├── style.css              # Apple VisionOS Liquid Glass 设计系统 + 暗色模式
│       │   ├── bootstrap-icons.css    # Bootstrap Icons（本地托管）
│       │   └── fonts/
│       │       ├── bootstrap-icons.woff2
│       │       └── bootstrap-icons.woff
│       └── js/
│           ├── app.js                 # 全局状态 + API 封装 + Toast
│           ├── htmx.min.js            # HTMX（本地托管）
│           └── alpine.min.js          # Alpine.js（本地托管）
│
└── data/                          # SQLite 数据库文件（运行时生成）
```

---

## 四、数据库模型

### ER 关系

```
users ──< records ──< approvals
  │                    │
  └──< audit_logs      └── users（审核人）
  │
items ──< records
```

### 表结构

#### users（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| username | TEXT UNIQUE | 登录用户名 |
| password_hash | TEXT | PBKDF2-SHA256 密码哈希 |
| display_name | TEXT | 显示名称 |
| role | TEXT CHECK(admin/approver/user) | 角色 |
| email | TEXT | 邮箱 |
| phone | TEXT | 手机号 |
| is_active | INTEGER | 启用=1，停用=0 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### items（物品表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| name | TEXT | 物品名称 |
| category | TEXT | 分类 |
| description | TEXT | 描述 |
| location | TEXT | 存放位置 |
| image_url | TEXT | OSS 图片 URL |
| total_quantity | INTEGER | 总库存数量 |
| status | TEXT CHECK(可用/租借中/损坏) | 实时计算状态 |
| value | REAL | 单价（元） |
| low_stock_threshold | INTEGER | 低库存预警阈值 |
| created_at / updated_at | TEXT | 时间戳 |

#### records（租借记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| item_id | INTEGER FK→items | 物品 ID |
| borrower_id | INTEGER FK→users | 借用人 ID |
| borrower_name | TEXT | 借用人姓名（冗余） |
| contact | TEXT | 联系方式 |
| quantity | INTEGER | 借出数量 |
| borrow_date | TEXT | 借出日期 |
| expected_return_date | TEXT | 预计归还日期 |
| actual_return_date | TEXT | 实际归还日期（完全归还时填写） |
| reason | TEXT | 租借事由 |
| return_notes | TEXT | 归还备注 |
| status | TEXT CHECK | 状态机驱动（见第五章） |
| approval_deadline | TEXT | 审核截止时间 |
| original_record_id | INTEGER FK→records | 部分归还拆分追溯 |
| created_by | INTEGER FK→users | 创建人 |
| created_at / updated_at | TEXT | 时间戳 |

#### approvals（审核记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| record_id | INTEGER FK→records | 关联租借记录 |
| approver_id | INTEGER FK→users | 审核人 ID |
| action | TEXT CHECK(approved/rejected) | 审核动作 |
| comment | TEXT | 审核意见 |
| ai_suggestion | TEXT | AI 审核建议（可选） |
| deadline | TEXT | 审核时限 |
| created_at | TEXT | 审核时间 |

#### audit_logs（操作日志表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| user_id | INTEGER FK→users | 操作人 ID |
| username | TEXT | 操作人用户名（冗余） |
| action | TEXT | 操作类型 |
| target_type | TEXT | 操作对象类型（record/item/user） |
| target_id | INTEGER | 操作对象 ID |
| detail | TEXT | 操作详情 |
| ip_address | TEXT | 操作 IP |
| created_at | TEXT | 操作时间 |

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
         审核通过    超时提醒    审核驳回（须填原因）
              │                    │
              ▼                    ▼
         ┌─────────┐         ┌──────────┐
         │  借出中   │         │  已拒绝   │ ──► 重新提交 → 待审核
         └────┬────┘         └──────────┘
              │
     ┌────────┼────────┐
     │        │        │
 完全归还   部分归还   超期
     │        │    (自动检测)
     ▼        ▼        ▼
┌────────┐ ┌───────┐ ┌──────┐
│ 已归还  │ │借出中  │ │ 逾期  │ ──► 归还 → 借出中/已归还
└────────┘ │(部分)  │ └──────┘
           └───────┘
```

### 合法转换表

| 当前状态 | 事件 | 目标状态 | 前置条件 |
|---------|------|---------|---------|
| (初始) | submit_borrow | 待审核 | 库存充足 |
| 待审核 | approve | 借出中 | 审核人权限 |
| 待审核 | reject | 已拒绝 | 必填驳回原因 |
| 已拒绝 | resubmit | 待审核 | 用户本人操作 |
| 借出中 | return_full | 已归还 | 归还数量 = 借出数量 |
| 借出中 | return_partial | 借出中 | 归还数量 < 借出数量 |
| 借出中 | auto_overdue | 逾期 | 超期未还 |
| 逾期 | return_full/return_partial | 已归还/逾期 | 同上 |

### 审核超时机制

- 申请进入"待审核"时，设置 `approval_deadline = now + APPROVAL_TIMEOUT_HOURS`
- 查询待审核列表时自动检测超时并标注
- 超时不自动拒绝，仅提醒

### 物品状态

物品状态由 `inventory_service` 实时计算：

```
可用 = total_quantity - SUM(借出中 + 逾期 + 待审核记录数量) > 0
租借中 = 上述差值 <= 0
损坏 = 管理员手动标记（不参与自动计算）
```

---

## 六、API 路由

### 认证 `/api/v1/auth`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /login | 登录，返回 JWT | 公开 |
| GET | /me | 当前用户信息 | 登录用户 |
| PUT | /change-password | 修改密码 | 登录用户 |

### 用户管理 `/api/v1/users`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | / | 用户列表（分页/搜索） | admin |
| POST | / | 创建用户 | admin |
| GET | /{id} | 用户详情 | admin |
| PUT | /{id} | 更新用户信息 | admin |
| PUT | /{id}/toggle | 启用/停用 | admin |
| PUT | /{id}/reset-password | 重置密码（→123456） | admin |

### 物品管理 `/api/v1/items`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | / | 物品列表（搜索/分类/状态/分页） | 登录用户 |
| GET | /categories | 分类列表 | 登录用户 |
| GET | /{id} | 物品详情（含实时库存） | 登录用户 |
| POST | / | 新增物品 | admin/approver |
| PUT | /{id} | 更新物品 | admin/approver |
| DELETE | /{id} | 删除（无活跃记录时） | admin |
| PUT | /{id}/mark-damaged | 标记损坏 | admin/approver |
| PUT | /{id}/mark-available | 恢复可用 | admin/approver |

### 租借记录 `/api/v1/records`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | / | 记录列表（筛选/分页） | 登录用户（普通用户仅见自己） |
| GET | /{id} | 记录详情 | 登录用户 |
| POST | / | 提交租借申请 | user |
| PUT | /{id}/resubmit | 驳回后重新提交 | user（仅自己） |
| PUT | /{id}/return | 归还（支持部分） | admin/approver |

### 审核 `/api/v1/approvals`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | /pending | 待审核列表（含超时标记） | admin/approver |
| GET | /stats | 审核统计 | admin/approver |
| PUT | /{id}/approve | 审核通过 | admin/approver |
| PUT | /{id}/reject | 驳回（必填原因） | admin/approver |
| GET | /{id}/history | 审核历史 | 登录用户 |

### 统计与日志

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | /api/v1/stats | 仪表盘统计 | 登录用户 |
| GET | /api/v1/logs | 操作日志（筛选/分页） | admin/approver |

### 前端页面路由

| 路径 | 页面 | 权限 |
|------|------|------|
| / / /login | 登录页 | 公开 |
| /dashboard | 仪表盘 | 登录用户 |
| /items | 物品管理 | 登录用户 |
| /records | 租借记录 | 登录用户 |
| /approvals | 审核管理 | admin/approver |
| /users | 用户管理 | admin |
| /logs | 操作日志 | admin |

---

## 七、前端技术栈

| 技术 | 用途 | 引入方式 |
|------|------|---------|
| Jinja2 | 模板渲染 | 服务端 |
| HTMX 2.0 | 无刷新页面交互（预留） | 本地 `/static/js/htmx.min.js` |
| Alpine.js 3.14 | 客户端状态管理 | 本地 `/static/js/alpine.min.js` |
| Bootstrap Icons 1.11 | 图标 | 本地 `/static/css/bootstrap-icons.css` |
| System Fonts | 字体 | 系统字体栈（`-apple-system, sans-serif` 等） |
| Apple VisionOS Liquid Glass CSS | 设计系统 + 暗色模式 | 自定义 style.css |

前端 JS 全局对象 `AppState` 管理认证状态和主题切换，`api()` 函数封装了带 JWT 的 fetch 请求。

---

## 八、关键设计说明

### 库存一致性

所有库存变更操作使用 SQLite `BEGIN IMMEDIATE` 事务模式：
1. 开启 IMMEDIATE 事务
2. 查询总库存 - 实时计算已占用数量
3. 检查可用量是否满足请求
4. 满足则提交，不满足则回滚

### 状态机集成

业务服务层禁止直接修改 `status` 字段，必须通过状态机：

```python
from app.state_machine.transitions import can_transition, transition

if not can_transition(record["status"], "approve"):
    raise ValueError("非法状态转换")

new_status = transition(record["status"], "approve")
conn.execute("UPDATE records SET status = ? WHERE id = ?", (new_status, record_id))
```

### RBAC 权限

通过 FastAPI `Depends` 依赖注入实现：

```python
# 角色检查依赖工厂
def require_role(*roles: str):
    def checker(current_user = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(403, "权限不足")
        return current_user
    return checker

# 使用
@router.post("/")
def create_item(current_user = Depends(require_role("admin", "approver"))):
    ...
```

### 第三方服务适配器

所有外部服务通过抽象基类封装，支持配置开关：

```
有配置 → 真实适配器（DeepSeekAdapter / AliyunOSSAdapter / AliyunSMSAdapter）
无配置 → Null 适配器（仅打日志，不报错）
```

### 密码安全

- 密码存储：PBKDF2-SHA256（10 万次迭代，随机盐）
- JWT 令牌：HS256 签名，24 小时过期
- 令牌验证：FastAPI `Depends(get_current_user)` 自动校验

---

## 九、部署说明

### 开发环境

```bash
python run.py
# 访问 http://localhost:8000
```

### 生产环境

```bash
uvicorn run:app --host 0.0.0.0 --port 8000 --workers 4
```

注意事项：
- 修改 `.env` 中的 `SECRET_KEY` 为强随机值
- SQLite 适用于单机部署，多实例部署建议迁移至 PostgreSQL
- 配置外部服务（DeepSeek / OSS / SMS）以启用 AI 审核、图片存储、短信通知

---

## 十、架构图

```
┌─────────────────────────────────────────────────────┐
│                    表现层 (Frontend)                   │
│  login.html  dashboard.html  items.html  records.html │
│  approvals.html  users.html  logs.html               │
│  Jinja2 + HTMX + Alpine.js + Apple VisionOS Liquid Glass CSS │
└────────────────────────┬────────────────────────────┘
                         │ HTTP / JWT
┌────────────────────────▼────────────────────────────┐
│                   应用层 (FastAPI)                     │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ 认证授权  │  │ 租借引擎   │  │ 审核工作流        │  │
│  │ JWT+RBAC │  │ borrow_svc│  │ approval_svc     │  │
│  └──────────┘  └───────────┘  └──────────────────┘  │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ 状态机    │  │ 库存服务   │  │ 通知服务          │  │
│  │ state_mch│  │ inventory  │  │ notification     │  │
│  └──────────┘  └───────────┘  └──────────────────┘  │
└────────────────────────┬────────────────────────────┘
                         │ SQL
┌────────────────────────▼────────────────────────────┐
│                   数据层 (SQLite)                      │
│  users  items  records  approvals  audit_logs        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              接口层 (Adapters 适配器)                  │
│  DeepSeek AI  │  阿里云 OSS  │  阿里云 SMS            │
│  (智能审核)    │  (图片存储)   │  (短信通知)            │
│  未配置 → NullAdapter 降级，不报错                     │
└─────────────────────────────────────────────────────┘
```

---

## 十一、已知问题与解决方案

### SQLite 线程亲和性

**问题：** FastAPI 对同步路由使用 `run_in_threadpool` 在线程池中执行，导致 `get_db()` 生成器在**线程 A** 创建连接，**线程 B** 关闭连接，触发 `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`。

**解决：** `app/database.py` 中 `get_connection()` 的 `sqlite3.connect()` 添加了 `check_same_thread=False`。项目已启用 WAL 模式，SQLite 自身序列化锁机制保证数据安全，该参数仅移除 Python 层面的线程检查，不影响数据一致性。

### 前端资源本地化

**问题：** `base.html` 中原先通过 CDN 加载 Google Fonts、Bootstrap Icons、HTMX、Alpine.js。Google Fonts 在中国大陆被 GFW 封锁，浏览器加载 `<head>` 中的 CSS `<link>` 时会白屏等待 TCP 超时（30s+），导致所有页面打开极慢。

**解决：** 删除 Google Fonts（CSS 中已有系统字体 fallback），其他三个库下载到 `frontend/static/` 本地托管，页面响应时间从几十秒降至毫秒级。
