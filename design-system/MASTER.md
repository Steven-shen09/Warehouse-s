# Warehouse-s 设计系统 — Cursor Warm Minimal

> 风格名称：**Cursor Warm Minimal**
> 最后更新：2026-05-22
> 适用范围：Warehouse-s 项目所有页面

---

## 一、风格定义

基于 Cursor 编辑器的暖色极简设计语言。强调**温暖纸质触感、极简无装饰、色彩层次代替光影层次**。不使用任何模糊、透明、渐变或动画效果。

**关键词：** Warm Minimalism、Paper Texture、Flat Surfaces、Warm Neutrals、Ink & Craft

**参考：** Cursor Editor、Cursor-showcase.html、精装印刷品设计

---

## 二、色彩系统

### 2.1 主色调

| 用途 | 变量 | 值 |
|------|------|-----|
| 主色（Apple蓝） | `--primary` | `#5B8CFF` |
| 主色深 | `--primary-dark` | `#4A7AF0` |
| 主色浅 | `--primary-light` | `#8DB5FF` |
| 点缀色（冰川紫） | `--accent` | `#8B7CFF` |
| 点缀色深 | `--accent-dark` | `#7B6AF0` |

**主色渐变（用于标题/按钮/数据数字）：** `linear-gradient(135deg, #5B8CFF, #8B7CFF)`

### 2.2 功能色

| 用途 | 变量 | 值 |
|------|------|-----|
| 成功 | `--success` | `#34C759` |
| 警告 | `--warning` | `#FF9F0A` |
| 危险 | `--danger` | `#FF453A` |
| 信息 | `--info` | `#64D2FF` |

### 2.3 文字颜色（亮色模式）

| 用途 | 变量 | 值 | 适用场景 |
|------|------|-----|---------|
| 标题色 | `--text-title` | `#111827` | 区块标题 |
| 正文 | `--text` | `rgba(17,24,39,0.88)` | 表格/正文 |
| 次级文字 | `--text-secondary` | `rgba(31,41,55,0.56)` | 标签/描述 |
| 辅助文字 | `--text-muted` | `rgba(31,41,55,0.40)` | 提示/占位 |

### 2.4 背景与表面（亮色模式）

| 用途 | 变量 | 值 |
|------|------|-----|
| 页面背景 | `--bg` | `#F4F8FF` |
| 页面背景（柔） | `--bg-soft` | `#EEF4FF` |
| 卡片背景 | `--bg-card` | `rgba(255,255,255,0.18)` |
| 卡片悬停 | `--bg-card-hover` | `rgba(255,255,255,0.32)` |
| 侧边栏 | `--bg-sidebar` | `rgba(255,255,255,0.12)` |
| 顶部导航 | `--bg-header` | `rgba(244,248,255,0.35)` |
| 输入框背景 | - | `rgba(255,255,255,0.14)` |
| 输入框边框 | - | `rgba(255,255,255,0.28)` |

### 2.5 暗色模式

| 用途 | 变量 | 值 |
|------|------|-----|
| 背景 | `--bg` | `#0a0e1a` |
| 卡片 | `--bg-card` | `rgba(20,28,60,0.35)` |
| 标题 | `--text-title` | `rgba(255,255,255,0.92)` |
| 正文 | `--text` | `rgba(255,255,255,0.88)` |
| 次级 | `--text-secondary` | `rgba(255,255,255,0.72)` |
| 辅助 | `--text-muted` | `rgba(255,255,255,0.48)` |
| 边框 | `--border` | `rgba(255,255,255,0.12)` |

---

## 三、玻璃效果

### 3.1 玻璃令牌

| 用途 | 变量 | 值 |
|------|------|-----|
| 标准玻璃背景 | `--glass-bg` | `rgba(255,255,255,0.18)` |
| 强玻璃背景 | `--glass-bg-strong` | `rgba(255,255,255,0.28)` |
| 玻璃边框 | `--glass-border` | `rgba(255,255,255,0.35)` |
| 玻璃高光 | `--glass-highlight` | `rgba(255,255,255,0.7)` |
| 卡片 blur | `--glass-blur` | `blur(16px)` |
| 导航栏 blur | `--blur-nav` | `blur(24px)` |
| 侧边栏 blur | `--glass-blur-strong` | `blur(30px)` |
| 模态框 blur | `--blur-modal` | `blur(40px)` |

### 3.2 玻璃效果清单

- **全边框折射高光**：所有卡片使用 `mask-composite: exclude` 技术，1px 渐变边框（`rgba(255,255,255,.7) → .05`），模拟玻璃边缘光学折射
- **液态扫光**：卡片 hover 时 `skewX(-20deg)` 斜切光带从左侧扫描至右侧（1.2s）
- **噪点纹理**：`body::after` 使用 SVG `feTurbulence` 生成 fractalNoise，`opacity: 0.025`，模拟真实玻璃表面
- **背景光晕**：5 层径向渐变 + `background-size: 200%` + 20s 循环流动动画

---

## 四、字体系统

### 4.1 字体栈

```css
--font-sans: "SF Pro Display", "PingFang SC", "Noto Sans SC", -apple-system, sans-serif;
--font-mono: "SF Mono", "Fira Code", "Cascadia Code", monospace;
```

### 4.2 字号层级

| 层级 | 元素 | 字号 | 字重 | 行高 | 字间距 | 颜色 |
|------|------|------|------|------|--------|------|
| 页面大标题 | `.main-content h2` | 34px | 700 | - | -0.03em | 蓝紫渐变 |
| 数据数字 | `.stat-value` | 42px | 700 | 1 | -0.03em | 蓝紫渐变 |
| 区块标题 | `.card-title` | 20px | 600 | - | -0.2px | `--text-title` |
| 导航品牌 | `.navbar-brand` | 20px | 600 | - | -0.3px | 蓝紫渐变 |
| 按钮 | `.btn` | 15px | 600 | - | -0.2px | 白色/彩色 |
| 表格正文 | `.table` | 15px | 500 | - | - | `--text` |
| 侧边栏 | `.sidebar a` | 14px | 500 | - | - | `--text-secondary` |
| 卡片标签 | `.stat-label` | 14px | 500 | - | 0.02em | `--text-secondary` |
| 表单标签 | `.form-label` | 14px | 500 | - | -0.1px | `--text-secondary` |
| 输入框 | `.form-input` | 15px | 500 | - | - | `--text` |
| 次级文字 | - | 13px | 400 | - | - | `--text-muted` |
| 状态标签 | `.status-badge` | 12px | 600 | - | -0.1px | 对应状态色 |

---

## 五、圆角与阴影

### 5.1 圆角

| 级别 | 变量 | 值 |
|------|------|-----|
| 大圆角 | `--radius-lg` | `28px` |
| 标准 | `--radius` | `24px` |
| 小圆角 | `--radius-sm` | `14px` |
| 极小 | `--radius-xs` | `10px` |

### 5.2 阴影（蓝色调 + 内发光）

| 级别 | 变量 | 值 |
|------|------|------|
| 标准 | `--shadow` | `0 4px 20px rgba(120,160,255,.10), inset 0 1px 0 rgba(255,255,255,.35)` |
| 大 | `--shadow-lg` | `0 12px 40px rgba(120,160,255,.12), inset 0 1px 0 rgba(255,255,255,.25)` |
| 抬起 | `--shadow-raised` | `0 8px 32px rgba(120,160,255,.16), inset 0 1px 0 rgba(255,255,255,.20)` |
| 发光 | `--shadow-glow` | `0 0 40px rgba(91,140,255,.15), 0 0 80px rgba(139,124,255,.08)` |
| hover | `--shadow-hover` | `0 20px 50px rgba(91,140,255,.18), inset 0 1px 0 rgba(255,255,255,.15)` |

> 所有阴影使用蓝色调 `rgba(120,160,255,x)`，不采用灰色 `rgba(0,0,0,x)`。内发光 `inset 0 1px 0` 模拟玻璃表面微反射。

---

## 六、动画

| 动画 | 时长 | 缓动 | 说明 |
|------|------|------|------|
| 页面进入 | 500ms | cubic-bezier(.25,.1,.25,1) | fadeInUp |
| 子元素 stagger | 0-50ms 递增 | 同上 | 依次入场 |
| 卡片 hover 上浮 | 500ms | 同上 | translateY(-4px) scale(1.01) |
| 液态扫光 | 1.2s | 同上 | skewX 光带扫描 |
| 模态框进入 | 350ms | 同上 | scale(0.96→1) |
| Toast | 350ms | 同上 | translateX 滑入 |
| 背景光晕流动 | 20s | ease-in-out | bgFlow |
| 侧边栏高光扫描 | 1.5s | ease-in-out | liquidShimmer |
| 按钮按下 | 100ms | - | scale(0.98) |

---

## 七、布局结构

```
┌──────────────────────────────────────────────────┐
│  .navbar (60px) — blur(24px) 玻璃导航             │
├────────┬─────────────────────────────────────────┤
│.sidebar│  .main-content                          │
│240px   │  padding: 28px 32px                     │
│blur:   │                                         │
│30px    │  卡片: blur(16px)                        │
│        │  模态框: blur(40px)                      │
└────────┴─────────────────────────────────────────┘
```

- 背景：`body::before` 5 层径向渐变 (200% size) + `body::after` SVG 噪点纹理
- 侧边栏底部自动分隔（最后一个 a 标签 `margin-top: auto`）

---

## 八、组件速查

### 8.1 按钮

```html
<button class="btn btn-primary">主操作</button>    <!-- 蓝紫渐变 15px/600 -->
<button class="btn btn-success">通过</button>       <!-- 绿色渐变 -->
<button class="btn btn-danger">删除</button>        <!-- 红色渐变 -->
<button class="btn btn-warning">警告</button>       <!-- 橙色渐变 -->
<button class="btn btn-outline">取消</button>       <!-- 玻璃边框 -->
<button class="btn btn-primary btn-sm">小按钮</button>  <!-- 12px -->
```

所有按钮 hover 时 `::after` 出现顶部高光 + `translateY(-1px)` 上浮。

### 8.2 模态框

```html
<!-- 遮罩: rgba(10,20,50,0.20) + blur(12px) -->
<div class="modal-overlay" id="xxx-modal">
  <!-- 卡片: rgba(255,255,255,0.80) + blur(40px) + 边缘折射高光 -->
  <div class="modal">
    <div class="modal-header"><h3>标题</h3></div>
    <div class="modal-body">内容</div>
    <div class="modal-footer">按钮</div>
  </div>
</div>
```

JS: `openModal(id)` / `closeModal(id)`，定义在 `app.js`

模态框遮罩使用蓝调半透明 `rgba(10,20,50,0.20)` 而非纯黑，卡片背景 `rgba(255,255,255,0.80)` 较亮以确保内容清晰可读。

### 8.3 统计卡片

```html
<div class="stat-card">
  <div class="stat-value">128</div>    <!-- 42px/700 蓝紫渐变 -->
  <div class="stat-label">物品总数</div> <!-- 14px/500 -->
</div>
```

### 8.4 表格

```html
<table class="table">               <!-- 15px/500 -->
  <thead><tr><th>列名</th></tr></thead>  <!-- 13px/600 -->
  <tbody><tr><td>...</td></tr></tbody>
</table>
```

### 8.5 空状态

所有页面空状态使用 Bootstrap Icons 矢量图标（非 emoji）：

| 页面 | 图标类 | 文案 |
|------|--------|------|
| 仪表盘 | `bi-journal-text` | 暂无租借记录 |
| 物品管理 | `bi-box` | 暂无物品 |
| 租借记录 | `bi-journal-text` | 暂无租借记录 |
| 审核管理 | `bi-clipboard-check` | 暂无待审核记录 |
| 用户管理 | `bi-people` | 暂无用户 |
| 操作日志 | `bi-clock-history` | 暂无操作日志 |

```html
<div class="empty-state">
  <div class="icon"><i class="bi bi-box"></i></div>
  <p>暂无物品</p>
</div>
```

### 8.6 状态标签

```html
<span class="status-badge available">可用</span>
<!-- available / lent / damaged / pending / approved / rejected / returned / overdue -->
```

---

## 九、硬约束

- **禁止** `confirm()` / `prompt()` / `alert()` — 使用自定义模态框
- **禁止** 外部 CDN 引用 — 所有资源本地托管
- **禁止** 内联 style 硬编码颜色 — 使用 CSS 变量
- **禁止** emoji 作为图标 — 使用 Bootstrap Icons
- **设计风格固定** — 本项目使用 Apple VisionOS Liquid Glass，不混入其他风格
- **卡片透明度** — 保持 0.18 级别，不要恢复到 0.45 以上
- **阴影颜色** — 使用蓝色调，不要使用纯灰色阴影

---

## 十、文件位置

| 文件 | 用途 |
|------|------|
| `frontend/static/css/style.css` | 主设计系统 |
| `frontend/static/css/login.css` | 登录页 |
| `frontend/static/css/bootstrap-icons.css` | 图标库 |
| `frontend/templates/base.html` | 布局骨架 |
| `design-system/MASTER.md` | 本文档 — 设计规范 |
