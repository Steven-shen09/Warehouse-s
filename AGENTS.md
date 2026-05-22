# AGENTS.md

此文件为 Codex 在 Warehouse-s 项目中工作时提供指引。

## 强制工作流（最高优先级，不可跳过）

**触发规则基于操作类型（客观事实），不基于主观判断（"简单/复杂"）。**

### 开工前强制自检

**每次收到代码修改请求，回复的第一句话必须是：**

```
🔍 任务类型：[新功能 / Bug / UI / 数据 / 重构]
📋 适用流程：[对应 AGENTS.md 工作流]
✅ 前置条件：[已调用的 skill 名称]
```

**三项缺一不可。未完成自检前，禁止调用 Edit / Write / Bash 修改文件。**

| 触发条件 | 必须调用 | 说明 |
|----------|---------|------|
| 调用 `Edit` 或 `Write` | `brainstorming`（首次该任务） | 修改代码前先过方案 |
| 调用 `EnterPlanMode` | `brainstorming`（如果还没调） | 规划前必须先探索 |
| 用户提到 bug/报错/异常 | `systematic-debugging` | 复现→最小化→假设→测量→修复→回归测试 |
| 涉及 CSS/HTML/模板/Jinja2 | `brainstorming` + `frontend-design` | 结果必须符合 Apple Liquid Glass 设计规范（见 memory: apple_liquid_glass_design） |
| 新增文件/函数/路由/API | `writing-plans` 或 `/plan` | 先出方案再动手 |
| 写实现代码前 | `superpowers:test-driven-development` | 先写测试→红灯→绿灯→重构 |
| 提交代码前 | `security-review` | 检查 JWT、RBAC、密码哈希、SQL 注入、XSS |

**流程顺序**：
```
触发条件匹配 → 调用对应技能 → 确认方案 → 开始改代码
```

**违反任何一条，立即停止，回到触发条件匹配步骤。**

---

> **设计优先参考**: [`warehouse.txt`](./warehouse.txt) — 物品租借系统方案文档，任何设计、修改、新增功能前必须先阅读此文档。

## 项目概述

全栈物品租借管理系统。后端 Python FastAPI + SQLite（WAL 模式），前端 Jinja2 + HTMX 2.0 + Alpine.js 3.14，**Apple Liquid Glass** 设计系统（支持暗色模式），安全方案 PBKDF2-SHA256 + JWT (HS256)。

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
- **ui-ux-pro-max** — 优化 Apple Liquid Glass 设计系统、暗色模式、响应式布局、组件交互时使用。

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
- 版本号规则：每次推送 GitHub 时版本号 +0.1（v1.1 → v1.2 → v1.3 ...）。

## 设计系统 — Cursor Warm Minimal

> 完整设计规范见 [`design-system/MASTER.md`](./design-system/MASTER.md)
> 风格：温暖纸质触感 · 极简无装饰 · 色彩层次代替光影层次

### 配色（Cursor Warm Minimal）

CSS 变量定义在 `frontend/static/css/style.css :root` 中：

| 用途 | 变量 | 亮色值 |
|------|------|--------|
| 主色（Cursor橙） | `--primary` | `#F54E00` |
| 点缀色（暖金） | `--accent` | `#C08532` |
| 页面背景 | `--bg` | `#F2F1ED` |
| 卡片背景 | `--bg-card` | `#E6E5E0` |
| 标题文字 | `--text-title` | `#26251E` |
| 正文 | `--text` | `#26251E` |
| 次级文字 | `--text-secondary` | `rgba(38,37,30,0.56)` |
| 辅助文字 | `--text-muted` | `rgba(38,37,30,0.40)` |
| 圆角 | `--radius` | `14px` |
| 阴影（仅hover） | `--shadow-hover` | `0 2px 16px rgba(38,37,30,0.06)` |

### 字号层级

| 层级 | 元素 | 字号/字重 |
|------|------|----------|
| 页面大标题 | `.main-content h2` | 44px / 700 |
| 数据数字 | `.stat-value` | 42px / 700 |
| 区块标题 | `.card-title` | 20px / 600 |
| 按钮/表格/输入框 | `.btn` `.table` `.form-input` | 14px / 500 |
| 侧边栏/标签 | `.sidebar a` `.stat-label` | 13px / 500 |
| 次级文字 | — | 13px / 400 |

### 平面设计原则

本设计系统不使用模糊（blur）、渐变（gradient）、噪点纹理（SVG feTurbulence）、液态扫光动画。以色彩层次代替光影层次：

- **无模糊**：导航栏、侧边栏、卡片、模态框均为纯色背景，不使用 backdrop-filter: blur()
- **无渐变**：标题、按钮、数据数字使用纯色填充，不应用 linear-gradient()
- **无噪点纹理**：移除 body::after SVG feTurbulence 纹理叠加
- **无液态扫光**：移除 hover 时 skewX 斜切光带扫描动画
- **无阴影内发光**：不添加 inset 阴影模拟玻璃微反射，仅 hover 时使用轻微暖棕色 box-shadow
- **无背景光晕**：不使用径向渐变背景动画

动画方面，仅保留必要的交互反馈（hover 过渡、页面进入 fadeIn），不使用扫光、流动等装饰性动画。

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
