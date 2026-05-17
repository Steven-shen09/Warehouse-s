# CLAUDE.md

此文件为 Claude Code 在 Warehouse-s 项目中工作时提供指引。

> **设计优先参考**: [`warehouse.txt`](./warehouse.txt) — 物品租借系统方案文档，任何设计、修改、新增功能前必须先阅读此文档。

## 项目概述

全栈物品租借管理系统。后端 Python FastAPI + SQLite（WAL 模式），前端 Jinja2 + HTMX 2.0 + Alpine.js 3.14，Flat Design 自定义设计系统（支持暗色模式），安全方案 PBKDF2-SHA256 + JWT (HS256)。

详见 [DEV.md](./DEV.md) 和 [README.md](./README.md)。

## 推荐 Skills

以下 skills 已安装并适用于本项目，编写代码时主动参考：

### 编码质量
- **karpathy-guidelines** — 避免过度设计，精准修改，披露假设，定义可验证的成功标准。写任何代码前参考。
- **simplify** — 提交改动后复查代码的重用性、质量和效率，发现问题立即修复。
- **fullstack-developer** — 全栈开发通用指引，覆盖前后端协作模式。

### 调试
- **systematic-debugging** — 遇到 bug、测试失败或异常行为时使用，先排查再修复。

### 前端与 UI
- **frontend-design** — 创建/改进 Jinja2 模板页面时使用，生成有设计感的界面。
- **ui-ux-pro-max** — 优化 Flat Design 设计系统、暗色模式、响应式布局、组件交互时使用。

### 安全与审查
- **security-review** — 提交前审查 JWT、RBAC、密码哈希等安全相关变更。
- **review** — PR 审查。

### 测试与发布
- **gstack** — 无头浏览器端到端测试（登录流程、物品 CRUD、审核工作流等）。
- **release-skills** — 发布新版本、生成 Release Notes 时使用。

## 关键约定

- 状态变更必须通过 `app/state_machine/` 引擎，禁止业务服务层直接修改 `status` 字段。
- 库存操作使用 `BEGIN IMMEDIATE` 事务保护一致性。
- 第三方服务（DeepSeek AI / 阿里云 OSS / 阿里云 SMS）未配置时自动降级为空适配器，不报错。
- 所有前端资源本地托管，**不引入任何外部 CDN 依赖**。

## 设计系统

### 配色（柔和暖杏系 Flat Design）

CSS 变量定义在 `frontend/static/css/style.css :root` 中：

| 用途 | 变量 | 色值 |
|------|------|------|
| 主色 | `--primary` | `#c97d60` |
| 主色深 | `--primary-dark` | `#b06a4e` |
| 主色浅 | `--primary-light` | `#e0a68c` |
| 成功 | `--success` | `#5d9b62` |
| 危险 | `--danger` | `#c9635e` |
| 警告 | `--warning` | `#e09a4a` |
| 信息 | `--info` | `#7a9ec4` |
| 页面背景 | `--bg` | `#faf7f4` |
| 卡片背景 | `--bg-card` | `#fefdfc` |
| 侧边栏背景 | `--bg-sidebar` | `#3d2e26` |
| 正文字色 | `--text` | `#3d3028` |
| 圆角 | `--radius` | `12px` |
| 阴影 | `--shadow` | `0 4px 12px rgba(0,0,0,0.06)` |

暗色模式通过 `[data-theme="dark"]` 选择器切换，变量值在 `style.css` 第 50-63 行定义。

### 组件使用规范

**模态框** — 新建弹窗必须使用系统模态框组件：
```html
<div class="modal-overlay" id="xxx-modal">
  <div class="modal">
    <div class="modal-header">...</div>
    <div class="modal-body">...</div>
    <div class="modal-footer">...</div>
  </div>
</div>
```
JS 控制：`openModal(id)` / `closeModal(id)`，定义在 `frontend/static/js/app.js` 第 61-66 行。

**确认弹窗** — **禁止使用浏览器原生 `confirm()` 和 `prompt()`**，必须用自定义模态框实现。参考 `approvals.html` 的 `#confirm-modal` 和 `#reject-modal` 模式：
- 用 `showConfirmDialog(title, message, onConfirm)` 回调模式
- 取消按钮 `btn-outline`，确认按钮 `btn-success`（通过）/ `btn-danger`（驳回/危险操作）
- 驳回操作在弹窗内用 `<textarea>` 收集原因

**Toast 通知** — `showToast(message, type)` 定义在 `app.js` 第 43-58 行，type 可选 `'success'` / `'error'` / `'warning'`。

**按钮** — 使用 `.btn` 基类 + `.btn-primary` / `.btn-success` / `.btn-danger` / `.btn-outline` 等变体，支持 `.btn-sm` 小尺寸。

**表格** — 使用 `.table` 类，状态标签用 `.status-badge` + `.lent` / `.returned` / `.overdue` / `.pending` / `.rejected` / `.available` / `.damaged`。

**单据分组** — 使用 `.doc-group` > `.doc-group-header` + `.doc-group-body` 结构，分组可折叠展开。

### 前端硬约束

- **禁止** `confirm()` / `prompt()` / `alert()` — 必须使用自定义模态框
- **禁止** 外部 CDN 引用 — 所有 CSS/JS/字体本地托管
- **禁止** 内联 `style` 中写硬编码颜色 — 优先使用 CSS 变量
