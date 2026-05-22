# Cursor Warm Minimal 设计系统迁移实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Warehouse-s 前端 CSS 从 Apple VisionOS Liquid Glass 完整替换为 Cursor Warm Minimal（暖色极简平面风）

**Architecture:** 单文件 CSS 重写 — 替换 `:root` CSS 变量定义 + 重写所有组件的玻璃效果为平面实体样式。HTML 结构和 JS 逻辑不变。

**Tech Stack:** CSS3（CSS Variables、oklch/oklab）、Jinja2 模板、无额外依赖

**Spec:** `docs/superpowers/specs/2026-05-22-cursor-warm-design-system.md`

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `frontend/static/css/style.css` | 主设计系统（1265行） | 重写 |
| `design-system/MASTER.md` | 设计规范文档 | 更新 |
| `CLAUDE.md` | Claude Code 配置 | 更新设计描述 |
| `AGENTS.md` | Codex 配置 | 更新设计描述 |

所有修改仅限这4个文件，不改动模板 HTML、JS、后端代码。

---

### Task 1: 重写 CSS 变量层和基础重置

**Files:**
- Modify: `frontend/static/css/style.css:1-160`

将 `:root` 块、暗色模式 `[data-theme="dark"]` 块、body 伪元素（光晕+噪点）全部替换。

- [ ] **Step 1: 替换 `:root` 变量定义（第1-67行）**

```css
/* ── Warehouse-s Cursor Warm Minimal 设计系统 ── */

:root {
  /* 主色调 — Cursor 橙 + 暖金 */
  --primary: #F54E00;
  --primary-dark: #D94300;
  --primary-light: #FF7A33;
  --accent: #C08532;
  --accent-dark: #A06E28;
  --success: #1F8A65;
  --warning: #C08532;
  --danger: #CF2D56;
  --info: #9FBBE0;

  /* 中性色 — 暖米白纸感 */
  --bg: #F2F1ED;
  --bg-soft: #E6E5E0;
  --bg-card: #E6E5E0;
  --bg-card-hover: #EBEAE5;
  --bg-sidebar: #E6E5E0;
  --bg-header: #F2F1ED;
  --text-title: #26251E;
  --text: #26251E;
  --text-secondary: rgba(38,37,30,0.56);
  --text-muted: rgba(38,37,30,0.40);

  /* 边框（oklab 暖棕空间） */
  --border: oklab(0.263084 -0.00230259 0.0124794 / 0.1);
  --border-strong: oklab(0.263084 -0.00230259 0.0124794 / 0.2);
  --border-heavy: rgba(38,37,30,0.55);
  --border-light: oklab(0.263084 -0.00230259 0.0124794 / 0.06);
  --border-card: oklab(0.263084 -0.00230259 0.0124794 / 0.1);

  /* 状态颜色 */
  --status-available: #1F8A65;
  --status-lent: #9FBBE0;
  --status-damaged: #CF2D56;
  --status-pending: #C08532;
  --status-approved: #9FC9A2;
  --status-rejected: #CF2D56;
  --status-returned: #C0A8DD;
  --status-overdue: #F54E00;

  /* 字体 */
  --font-sans: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --font-mono: ui-monospace, 'SF Mono', 'Cascadia Code', monospace;

  /* 间距与圆角 */
  --radius: 14px;
  --radius-sm: 10px;
  --radius-xs: 8px;
  --radius-lg: 24px;

  /* 阴影（仅 hover 使用） */
  --shadow-hover: 0 2px 16px rgba(38,37,30,0.06);
  --transition: 0.2s ease;
}
```

- [ ] **Step 2: 删除暗色模式块（第69-93行）**

删除整个 `[data-theme="dark"]` 块（25行），不再支持暗色模式。

- [ ] **Step 3: 替换 body 伪元素（第100-159行）**

```css
/* ── 基础重置 ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { height: 100%; }

body {
  font-family: var(--font-sans);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

a { color: var(--primary); text-decoration: none; transition: var(--transition); }
a:hover { color: var(--primary-dark); }
```

删除所有 body::before（光晕）、body::after（噪点纹理）、@keyframes bgFlow。

- [ ] **Step 4: 提交**

```bash
git add frontend/static/css/style.css
git commit -m "feat: 替换 CSS 变量和基础重置为 Cursor Warm Minimal"
```

---

### Task 2: 重写导航栏

**Files:**
- Modify: `frontend/static/css/style.css:164-205`

- [ ] **Step 1: 替换导航栏样式**

```css
/* ── 导航栏 - 暖色实体条 ── */
.navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 28px; height: 60px;
  background: var(--bg-header);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
}
.navbar-brand {
  font-size: 20px; font-weight: 600;
  color: var(--text);
  display: flex; align-items: center; gap: 8px;
  letter-spacing: -0.3px;
}
.navbar-brand i {
  font-size: 24px;
  color: var(--primary);
}
.navbar-nav { display: flex; align-items: center; gap: 14px; list-style: none; }
.navbar-nav a, .navbar-nav span, .navbar-nav button {
  color: var(--text-secondary); font-size: 14px;
  padding: 6px 14px; border-radius: 20px;
  transition: var(--transition);
}
.navbar-nav a:hover { color: var(--primary); background: rgba(245,78,0,0.06); }

.badge-role {
  display: inline-block; padding: 3px 12px; border-radius: 20px;
  font-size: 12px; font-weight: 600;
  background: rgba(245,78,0,0.08);
  color: var(--primary);
  border: 1px solid rgba(245,78,0,0.15);
}
```

删除：`backdrop-filter`、`box-shadow`（含 inset 内发光）、蓝紫渐变文字。

- [ ] **Step 2: 提交**

```bash
git add frontend/static/css/style.css
git commit -m "feat: 重写导航栏为 Cursor 暖色实体风格"
```

---

### Task 3: 重写侧边栏

**Files:**
- Modify: `frontend/static/css/style.css:207-300`

- [ ] **Step 1: 替换侧边栏和主内容区样式**

```css
/* ── 布局 ── */
.layout {
  display: flex; min-height: calc(100vh - 60px);
  position: relative; z-index: 1;
}

/* ── 侧边栏 - 实色 ── */
.sidebar {
  width: 240px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  padding: 20px 0;
  flex-shrink: 0;
  display: flex; flex-direction: column;
}

.sidebar a {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 24px; margin: 2px 12px;
  color: var(--text-secondary);
  font-size: 13px; font-weight: 500;
  border-radius: 10px;
  transition: all 0.15s ease;
}

.sidebar a i {
  font-size: 18px;
  transition: transform 0.15s ease;
}

.sidebar a:hover, .sidebar a.active {
  color: var(--text);
  background: rgba(38,37,30,0.06);
}

.sidebar a.active {
  background: rgba(38,37,30,0.08);
  font-weight: 600;
}

.sidebar a:hover i { transform: scale(1.05); }

/* 侧边栏分隔 — 最后一项推到底 */
.sidebar a:last-of-type {
  margin-top: auto;
}

.main-content {
  flex: 1; padding: 28px 32px;
  overflow-x: auto;
  position: relative; z-index: 1;
  animation: fadeInUp 0.4s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
```

删除：`backdrop-filter`、`::before` 折射高光、`::before` 液态高光、`liquidShimmer` 动画、`box-shadow` 发光、蓝紫渐变激活背景。

- [ ] **Step 2: 提交**

```bash
git add frontend/static/css/style.css
git commit -m "feat: 重写侧边栏和主布局为实色风格"
```

---

### Task 4: 重写页面标题 + 卡片 + 统计卡片

**Files:**
- Modify: `frontend/static/css/style.css:306-490`

- [ ] **Step 1: 替换页面标题**

```css
/* ── 页面标题 ── */
.main-content h2 {
  font-size: 44px; font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 28px;
  color: var(--text-title);
}
```

去掉蓝紫渐变。

- [ ] **Step 2: 替换卡片组件**

```css
/* ── 卡片 ── */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  margin-bottom: 20px;
  transition: all 0.2s ease;
}
.card:hover {
  background: var(--bg-card-hover);
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}
.card-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px; padding-bottom: 14px;
  border-bottom: 1px solid var(--border-light);
}
.card-title {
  font-size: 20px; font-weight: 600; color: var(--text-title);
  letter-spacing: -0.2px;
}
```

删除：`backdrop-filter`、`::before` 折射高光、`::after` 液态扫光、`skewX` 变换。

- [ ] **Step 3: 替换统计卡片**

```css
/* ── 统计卡片 ── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 18px;
  margin-bottom: 28px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 20px;
  text-align: center;
  transition: all 0.2s ease;
  cursor: default;
}
.stat-card:hover {
  transform: translateY(-2px);
  background: var(--bg-card-hover);
  box-shadow: var(--shadow-hover);
}
.stat-card .stat-icon {
  font-size: 28px; margin-bottom: 6px; line-height: 1;
  color: var(--primary);
}
.stat-card .stat-value {
  font-size: 42px; font-weight: 700;
  color: var(--text);
  letter-spacing: -0.03em;
  line-height: 1;
}
.stat-card .stat-label {
  font-size: 13px; color: var(--text-secondary);
  margin-top: 8px; font-weight: 500;
}
.stat-card.clickable { cursor: pointer; }
.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
  border-color: var(--primary);
}
```

删除：`backdrop-filter`、`::before`/`::after` 伪元素、蓝紫渐变文字、`shadow-glow`、`scale(1.02)`。

- [ ] **Step 4: 提交**

```bash
git add frontend/static/css/style.css
git commit -m "feat: 重写页面标题、卡片、统计卡片为平面暖色风格"
```

---

### Task 5: 重写表格 + 状态标签

**Files:**
- Modify: `frontend/static/css/style.css:492-553`

- [ ] **Step 1: 替换表格样式**

```css
/* ── 表格 ── */
.table {
  width: 100%; border-collapse: separate; border-spacing: 0;
  font-size: 14px; font-weight: 500;
  border-radius: var(--radius-sm);
}
.table th, .table td {
  padding: 12px 16px; text-align: left;
  border-bottom: 1px solid var(--border-light);
}
.table th {
  font-weight: 600; color: var(--text-secondary);
  background: var(--bg-soft);
  font-size: 13px;
  letter-spacing: -0.1px;
}
.table tbody tr {
  transition: background 0.15s ease;
  background: transparent;
}
.table tbody tr:nth-child(even) {
  background: #F7F7F4;
}
.table tbody tr:hover {
  background: rgba(245,78,0,0.04);
}
.table td:first-child, .table th:first-child { padding-left: 20px; }
```

- [ ] **Step 2: 替换状态标签**

```css
/* ── 状态标签 ── */
.status-badge {
  display: inline-block; padding: 3px 12px; border-radius: 999px;
  font-size: 12px; font-weight: 600; white-space: nowrap;
  letter-spacing: -0.1px;
}
.status-badge.available {
  background: rgba(31,138,101,0.10); color: #1F8A65;
  border: 1px solid rgba(31,138,101,0.18);
}
.status-badge.lent {
  background: rgba(159,187,224,0.18); color: #5A7BA8;
  border: 1px solid rgba(159,187,224,0.30);
}
.status-badge.damaged {
  background: rgba(207,45,86,0.10); color: #CF2D56;
  border: 1px solid rgba(207,45,86,0.18);
}
.status-badge.pending {
  background: rgba(192,133,50,0.12); color: #C08532;
  border: 1px solid rgba(192,133,50,0.20);
}
.status-badge.approved {
  background: rgba(159,201,162,0.18); color: #5A8F62;
  border: 1px solid rgba(159,201,162,0.28);
}
.status-badge.rejected {
  background: rgba(207,45,86,0.10); color: #CF2D56;
  border: 1px solid rgba(207,45,86,0.18);
}
.status-badge.returned {
  background: rgba(192,168,221,0.18); color: #7B68A0;
  border: 1px solid rgba(192,168,221,0.28);
}
.status-badge.overdue {
  background: rgba(245,78,0,0.10); color: #F54E00;
  border: 1px solid rgba(245,78,0,0.20);
}
```

删除：`backdrop-filter`、所有 `[data-theme="dark"]` 状态标签样式。

- [ ] **Step 3: 提交**

```bash
git add frontend/static/css/style.css
git commit -m "feat: 重写表格和状态标签为暖色系"
```

---

### Task 6: 重写表单 + 按钮

**Files:**
- Modify: `frontend/static/css/style.css:555-663`

- [ ] **Step 1: 替换表单样式**

```css
/* ── 表单 ── */
.form-group { margin-bottom: 18px; }
.form-label {
  display: block; font-size: 14px; font-weight: 500;
  margin-bottom: 8px; color: var(--text-secondary);
  letter-spacing: -0.1px;
}
.form-input, .form-select, .form-textarea {
  width: 100%; padding: 11px 16px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  font-size: 14px; font-family: var(--font-sans); font-weight: 500;
  background: #FFFFFF;
  color: var(--text);
  transition: all 0.15s ease;
  outline: none;
}
.form-input:focus, .form-select:focus, .form-textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(245,78,0,0.10);
  background: #FFFFFF;
}
.form-textarea { resize: vertical; min-height: 80px; }
```

删除：`backdrop-filter`、玻璃半透明背景、蓝紫 focus 色、`[data-theme="dark"]` 表单样式。

- [ ] **Step 2: 替换按钮样式**

```css
/* ── 按钮 ── */
.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 18px; border: none; border-radius: 10px;
  font-size: 14.5px; font-weight: 500; cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  letter-spacing: -0.2px;
}
.btn:hover:not(:disabled) {
  filter: brightness(1.06);
  transform: translateY(-1px);
}
.btn:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
}
.btn:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-primary {
  background: var(--primary);
  color: #FFFFFF;
}
.btn-primary:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(245,78,0,0.20);
}
.btn-success {
  background: var(--success);
  color: #FFFFFF;
}
.btn-success:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(31,138,101,0.20);
}
.btn-danger {
  background: var(--danger);
  color: #FFFFFF;
}
.btn-danger:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(207,45,86,0.20);
}
.btn-warning {
  background: var(--warning);
  color: #FFFFFF;
}
.btn-warning:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(192,133,50,0.20);
}
.btn-outline {
  background: transparent;
  color: var(--text);
  border: 1px solid var(--border-strong);
}
.btn-outline:hover:not(:disabled) {
  background: rgba(245,78,0,0.04);
  border-color: var(--primary);
  color: var(--primary);
}
.btn-sm { padding: 5px 12px; font-size: 12px; border-radius: 8px; }
.btn-group { display: flex; gap: 8px; }
```

删除：`::after` 液态高光、蓝紫渐变背景、`backdrop-filter`、inset 阴影。

- [ ] **Step 3: 提交**

```bash
git add frontend/static/css/style.css
git commit -m "feat: 重写表单和按钮为暖色平面风格"
```

---

### Task 7: 重写搜索筛选 + 分页 + 模态框 + 确认弹窗

**Files:**
- Modify: `frontend/static/css/style.css:666-699, 811-878, 1213-1265`

- [ ] **Step 1: 替换搜索筛选栏**

```css
/* ── 搜索与筛选 ── */
.filter-bar {
  display: flex; gap: 12px; margin-bottom: 20px;
  flex-wrap: wrap; align-items: center;
}
.filter-bar .form-input, .filter-bar .form-select { width: auto; min-width: 160px; }
```

- [ ] **Step 2: 替换分页**

```css
/* ── 分页 ── */
.pagination {
  display: flex; gap: 6px; justify-content: center;
  margin-top: 20px;
}
.pagination button {
  padding: 8px 16px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text);
  border-radius: var(--radius-xs);
  cursor: pointer;
  font-size: 13px; font-weight: 500;
  transition: all 0.15s ease;
}
.pagination button:hover:not(:disabled) {
  background: rgba(245,78,0,0.06);
  color: var(--primary);
  border-color: var(--primary);
}
.pagination button.active {
  background: var(--primary);
  color: #fff; border-color: transparent;
}
.pagination button:disabled { opacity: 0.35; cursor: default; }
```

- [ ] **Step 3: 替换模态框**

```css
/* ── 模态框 ── */
.modal-overlay {
  display: none; position: fixed; inset: 0; z-index: 999;
  background: rgba(38,37,30,0.20);
  align-items: center; justify-content: center;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-overlay.active { display: flex; }

.modal {
  background: #FFFFFF;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 40px rgba(38,37,30,0.12);
  width: 90%; max-width: 540px;
  max-height: 85vh; overflow-y: auto;
  animation: modalIn 0.25s ease;
}

@keyframes modalIn {
  from { opacity: 0; transform: translateY(16px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-light);
}
.modal-header h3 { font-size: 18px; font-weight: 600; letter-spacing: -0.3px; }
.modal-body { padding: 24px; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border-light);
}
```

删除：`backdrop-filter`、`::before` 折射高光、蓝调遮罩、`shadow-glow`。

- [ ] **Step 4: 替换确认弹窗**

```css
/* ── 确认对话框样式 ── */
.custom-confirm-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(38,37,30,0.20);
  display: flex; align-items: center; justify-content: center;
  animation: fadeIn 0.2s ease;
}
.custom-confirm-dialog {
  background: #FFFFFF;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 40px rgba(38,37,30,0.12);
  padding: 28px 32px;
  max-width: 440px;
  width: 90%;
  animation: modalIn 0.25s ease;
}
.custom-confirm-dialog h3 {
  font-size: 18px; font-weight: 600; margin-bottom: 8px;
  letter-spacing: -0.3px;
}
.custom-confirm-dialog p {
  font-size: 14px; color: var(--text-secondary);
  margin-bottom: 20px; line-height: 1.5;
}
.custom-confirm-dialog textarea {
  width: 100%; margin-bottom: 16px;
  padding: 10px 14px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  font-size: 14px; font-family: var(--font-sans);
  background: var(--bg);
  color: var(--text);
  resize: vertical; min-height: 80px;
  outline: none;
}
.custom-confirm-dialog textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(245,78,0,0.08);
}
.custom-confirm-dialog .btn-row {
  display: flex; gap: 10px; justify-content: flex-end;
}
```

- [ ] **Step 5: 提交**

```bash
git add frontend/static/css/style.css
git commit -m "feat: 重写模态框、确认弹窗、分页为平面暖色风格"
```

---

### Task 8: 重写登录页 + Toast + 空状态 + 骨架屏 + 滚动条

**Files:**
- Modify: `frontend/static/css/style.css:702-903`

- [ ] **Step 1: 替换登录页**

```css
/* ── 登录页 ── */
.login-page {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh;
  position: relative;
  background: linear-gradient(180deg, #F2F1ED 0%, #E6E5E0 100%);
}

.login-card {
  width: 420px; padding: 48px 44px;
  background: #FFFFFF;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 40px rgba(38,37,30,0.08);
  position: relative;
  z-index: 1;
  animation: fadeInUp 0.5s ease;
}

.login-card h1 {
  text-align: center; margin-bottom: 8px;
  font-size: 24px; font-weight: 700;
  color: var(--text);
  letter-spacing: -0.5px;
}

.login-card .btn { width: 100%; justify-content: center; margin-top: 20px; }
.login-card .btn-primary { padding: 12px; font-size: 16px; border-radius: var(--radius-sm); }

.login-error {
  color: var(--danger); font-size: 13px; margin-top: 10px; text-align: center;
  display: none; font-weight: 500;
}

.login-card .demo-accounts {
  margin-top: 28px; padding-top: 18px;
  border-top: 1px solid var(--border-light);
}
.login-card .demo-accounts p {
  font-size: 12px; color: var(--text-muted); text-align: center;
  line-height: 1.8;
}
```

删除：`login-page::before` 光晕动画、`login-card::before` 折射高光、`backdrop-filter`、`@keyframes loginGlow`、`shadow-glow`、蓝紫渐变文字、`[data-theme="dark"]` 登录样式。

- [ ] **Step 2: 替换 Toast**

```css
/* ── Toast ── */
.toast-container {
  position: fixed; top: 76px; right: 28px; z-index: 9999;
}
.toast {
  padding: 14px 22px; margin-bottom: 8px;
  border-radius: var(--radius); color: #fff; font-size: 14px; font-weight: 500;
  box-shadow: 0 4px 20px rgba(38,37,30,0.12);
  animation: slideInToast 0.35s ease;
  border: 1px solid rgba(255,255,255,0.15);
}
.toast.success { background: var(--success); }
.toast.error { background: var(--danger); }
.toast.warning { background: var(--warning); }

@keyframes slideInToast {
  from { transform: translateX(120%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
```

删除：`backdrop-filter`、半透明背景。

- [ ] **Step 3: 替换空状态 + 骨架屏 + 滚动条**

```css
/* ── 空状态 ── */
.empty-state {
  text-align: center; padding: 56px 20px; color: var(--text-muted);
}
.empty-state .icon { font-size: 64px; margin-bottom: 14px; opacity: 0.4; }

/* ── 骨架屏加载 ── */
@keyframes shimmer {
  0% { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
.skeleton {
  background: linear-gradient(90deg,
    rgba(38,37,30,0.06) 25%,
    rgba(38,37,30,0.12) 50%,
    rgba(38,37,30,0.06) 75%);
  background-size: 800px 100%;
  animation: shimmer 1.8s ease-in-out infinite;
  border-radius: var(--radius-xs);
  min-height: 16px;
}

/* ── 滚动条美化 ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(38,37,30,0.15);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(38,37,30,0.25);
}
```

删除：`[data-theme="dark"]` 骨架屏和滚动条样式。

- [ ] **Step 4: 提交**

```bash
git add frontend/static/css/style.css
git commit -m "feat: 重写登录页、Toast、空状态、骨架屏为暖色平面风格"
```

---

### Task 9: 重写购物车面板 + 单据分组 + 工具类

**Files:**
- Modify: `frontend/static/css/style.css:905-1165`

- [ ] **Step 1: 替换工具类**

```css
/* ── 工具类 ── */
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-muted { color: var(--text-muted); }
.mt-8 { margin-top: 8px; }
.mt-16 { margin-top: 16px; }
.mb-8 { margin-bottom: 8px; }
.mb-16 { margin-bottom: 16px; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.gap-8 { gap: 8px; }
.flex { display: flex; }
.flex-wrap { flex-wrap: wrap; }
```

- [ ] **Step 2: 替换双栏布局**

```css
/* ── 双栏布局 ── */
.content-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}
.content-main {
  flex: 1;
  min-width: 0;
}
```

- [ ] **Step 3: 替换购物车面板**

所有 `rgba(255,255,255,x)` 的透明表面替换为实色变量，删除所有 `backdrop-filter`、`::before` 折射高光、蓝紫渐变文字（替换为 `var(--primary)` 纯色）。

```css
/* ── 购物车面板 ── */
.cart-sticky-wrapper {
  width: 380px;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  align-items: center;
}
.cart-panel {
  width: 100%;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}
.cart-panel-inner {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
}
.cart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border-light);
}
.cart-title {
  font-size: 16px; font-weight: 600; color: var(--text);
  display: flex; align-items: center; gap: 8px;
}
.cart-count-badge {
  display: inline-block; padding: 3px 12px; border-radius: 20px;
  font-size: 12px; font-weight: 600;
  background: rgba(245,78,0,0.08);
  color: var(--primary);
  border: 1px solid rgba(245,78,0,0.15);
}
.cart-empty {
  text-align: center; padding: 36px 16px; color: var(--text-muted);
}
.cart-empty .icon { font-size: 44px; opacity: 0.4; margin-bottom: 10px; }
.cart-items-list {
  display: flex; flex-direction: column; gap: 10px;
  max-height: 380px; overflow-y: auto; margin-bottom: 18px;
}
.cart-item {
  background: var(--bg);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 14px;
  transition: all 0.15s ease;
}
.cart-item:hover {
  box-shadow: var(--shadow-hover);
  background: #FFFFFF;
}
.cart-item-header {
  display: flex; justify-content: space-between;
  align-items: center; margin-bottom: 10px;
}
.cart-item-name {
  font-size: 14px; font-weight: 600; color: var(--text);
  flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.cart-item-remove {
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  font-size: 18px; line-height: 1; padding: 3px 8px;
  border-radius: var(--radius-xs); transition: all 0.2s ease;
}
.cart-item-remove:hover {
  color: var(--danger);
  background: rgba(207,45,86,0.08);
}
.cart-item-body {
  display: flex; align-items: center;
  justify-content: space-between; gap: 8px;
}
.cart-item-price {
  font-size: 13px; color: var(--text-muted); min-width: 60px;
}
.cart-quantity-control {
  display: flex; align-items: center; gap: 4px;
}
.cart-quantity-control button {
  width: 28px; height: 28px; padding: 0;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 14px; line-height: 1;
  border-radius: var(--radius-xs);
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text);
  cursor: pointer;
  transition: all 0.15s ease;
}
.cart-quantity-control button:hover:not(:disabled) {
  background: var(--primary);
  color: #fff; border-color: var(--primary);
}
.cart-quantity-control button:disabled {
  opacity: 0.35; cursor: not-allowed;
}
.cart-quantity-value {
  font-size: 14px; font-weight: 600;
  min-width: 30px; text-align: center;
}
.cart-item-subtotal {
  font-size: 15px; font-weight: 700;
  color: var(--primary);
  min-width: 70px; text-align: right;
}
.cart-summary {
  padding: 14px 0; margin-bottom: 18px;
  border-top: 2px solid var(--border);
  border-bottom: 1px solid var(--border-light);
}
.cart-summary-row {
  display: flex; justify-content: space-between;
  align-items: center; font-size: 14px; color: var(--text-secondary);
}
.cart-total-amount {
  font-size: 22px; font-weight: 700;
  color: var(--primary);
}
.cart-form .form-group { margin-bottom: 14px; }
.cart-form .form-label { font-size: 13px; }
.cart-form .form-input,
.cart-form .form-textarea { font-size: 13px; padding: 9px 14px; }
.table .col-check { width: 48px; text-align: center; }
.cart-checkbox {
  width: 17px; height: 17px; cursor: pointer;
  accent-color: var(--primary);
}
.cart-checkbox:disabled { cursor: not-allowed; opacity: 0.3; }
```

- [ ] **Step 4: 替换单据分组**

```css
/* ── 单据分组折叠 ── */
.doc-group {
  margin-bottom: 18px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--bg-card);
  transition: all 0.2s ease;
}
.doc-group:hover {
  box-shadow: var(--shadow-hover);
}
.doc-group-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 20px;
  background: var(--bg);
  cursor: pointer; user-select: none;
  transition: background 0.2s ease;
}
.doc-group-header:hover {
  background: var(--bg-card-hover);
}
.doc-group-actions {
  display: flex; gap: 8px; align-items: center;
}
.doc-group-actions .btn { font-size: 12px; padding: 5px 12px; }
.doc-group-toggle {
  font-size: 12px; color: var(--text-muted);
  margin-left: 8px; transition: transform 0.2s ease;
}
.doc-group-header.expanded .doc-group-toggle {
  transform: rotate(180deg);
}
.doc-group-body {
  padding: 0;
  border-top: 1px solid var(--border-light);
}
.doc-group-body .table { margin: 0; border-radius: 0; }
.doc-group-body .table th { background: var(--bg-soft); }
.doc-group-meta {
  display: flex; align-items: center; gap: 14px;
  flex-wrap: wrap;
}
.doc-group-meta strong {
  color: var(--primary);
  font-size: 15px;
}
```

- [ ] **Step 5: 替换低库存警告和其他杂项**

```css
/* ── 低库存警告 ── */
.low-stock-warn { color: var(--danger); font-weight: 700; }

/* ── 页面内容过渡动画 ── */
.main-content > * {
  animation: fadeInUp 0.4s ease both;
}
.main-content > *:nth-child(1) { animation-delay: 0s; }
.main-content > *:nth-child(2) { animation-delay: 0.04s; }
.main-content > *:nth-child(3) { animation-delay: 0.08s; }
.main-content > *:nth-child(4) { animation-delay: 0.12s; }
```

- [ ] **Step 6: 提交**

```bash
git add frontend/static/css/style.css
git commit -m "feat: 重写购物车、文档分组、工具类为暖色平面风格"
```

---

### Task 10: 更新设计规范文档和配置

**Files:**
- Modify: `design-system/MASTER.md`
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: 更新设计规范文档**

将 `design-system/MASTER.md` 的标题从 "Apple VisionOS Liquid Glass" 改为 "Cursor Warm Minimal"，完整替换色彩、字体、玻璃效果、组件等所有章节为新内容（参照 spec 文档）。

- [ ] **Step 2: 更新 CLAUDE.md**

替换 CLAUDE.md 第 80-119 行的 "设计系统 — Apple VisionOS Liquid Glass" 章节为 "设计系统 — Cursor Warm Minimal"。

- [ ] **Step 3: 更新 AGENTS.md**

同步更新 AGENTS.md 中相同章节内容。

- [ ] **Step 4: 提交**

```bash
git add design-system/MASTER.md CLAUDE.md AGENTS.md
git commit -m "docs: 更新设计规范文档为 Cursor Warm Minimal"
```

---

### Task 11: 删除 login.css 无用注释 + 最终验证

**Files:**
- Modify: `frontend/static/css/login.css`

- [ ] **Step 1: 清理 login.css**

将 login.css 更新为空注释（当前只是注释，无实际样式，login 样式在 style.css 中）。

- [ ] **Step 2: 验证 — 启动应用并检查**

```bash
cd c:/Users/slama/first-cc/Warehouse-s
python run.py &
sleep 2
# 检查关键页面：
# - GET / (登录页)：纯白卡片 + 暖米背景
# - GET /login：同上
# - GET /dashboard：暖色无玻璃效果
```

**Expected:** 所有页面无 glass/blur 效果，暖米白背景 + 暖棕文字 + 橙色点缀，无暗色模式痕迹，无背景光晕动画，无噪点纹理。

- [ ] **Step 3: 提交**

```bash
git add frontend/static/css/login.css
git commit -m "chore: 清理 login.css"
```

---

## 实施顺序

任务 1-9 是依赖链：必须按顺序执行，因为每个任务替换的 CSS 区域有前后依赖。任务 10-11 可并行或在最后执行。

```
Task 1 (CSS 变量 + 基础) → 重启应用验证颜色
  → Task 2 (导航栏)
  → Task 3 (侧边栏 + 布局)
  → Task 4 (标题 + 卡片 + 统计卡片)
  → Task 5 (表格 + 状态标签)
  → Task 6 (表单 + 按钮)
  → Task 7 (分页 + 模态框 + 确认弹窗)
  → Task 8 (登录页 + Toast + 空状态 + 骨架屏 + 滚动条)
  → Task 9 (购物车 + 单据分组 + 工具类)
  → Task 10 (设计文档更新) + Task 11 (验证)
```
