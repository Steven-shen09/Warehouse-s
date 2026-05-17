# Warehouse-s 设计系统 — Apple Liquid Glass

> 风格名称：**Apple Liquid Glass**
> 建立日期：2026-05-17
> 适用范围：Warehouse-s 项目所有页面

---

## 一、风格定义

Apple Liquid Glass 是一种融合了 Apple Vision Pro、iOS 18、macOS Sonoma 设计语言的玻璃拟态 UI 风格。核心特征是半透明毛玻璃卡片、柔和蓝紫渐变背景、液态高光反射、大圆角和漂浮式空间层次。

**关键词：** Glassmorphism、Liquid Glass、Frosted Glass、VisionOS、极简、通透、未来感

**参考：** Apple Vision Pro、iOS 18、macOS Sonoma、Arc Browser、Linear

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

### 2.2 功能色

| 用途 | 变量 | 值 |
|------|------|-----|
| 成功 | `--success` | `#34C759` |
| 警告 | `--warning` | `#FF9F0A` |
| 危险 | `--danger` | `#FF453A` |
| 信息 | `--info` | `#64D2FF` |

### 2.3 背景与表面

| 用途 | 变量 | 值（亮色模式） |
|------|------|---------------|
| 页面背景 | `--bg` | `#F4F8FF` |
| 页面背景（柔） | `--bg-soft` | `#EEF4FF` |
| 卡片背景 | `--bg-card` | `rgba(255,255,255,0.45)` |
| 卡片悬停 | `--bg-card-hover` | `rgba(255,255,255,0.65)` |
| 侧边栏 | `--bg-sidebar` | `rgba(255,255,255,0.25)` |
| 顶部导航 | `--bg-header` | `rgba(244,248,255,0.6)` |

### 2.4 暗色模式

暗色模式底色为 `#0a0e1a`（深蓝黑），玻璃面板透明度降低（卡 `rgba(20,28,60,0.55)`），文字反转但保持可读性。

---

## 三、玻璃效果

### 3.1 玻璃令牌

| 用途 | 变量 | 值 |
|------|------|-----|
| 标准玻璃背景 | `--glass-bg` | `rgba(255,255,255,0.45)` |
| 强玻璃背景 | `--glass-bg-strong` | `rgba(255,255,255,0.65)` |
| 玻璃边框 | `--glass-border` | `rgba(255,255,255,0.6)` |
| 玻璃高光 | `--glass-highlight` | `rgba(255,255,255,0.7)` |
| 标准模糊 | `--glass-blur` | `blur(20px)` |
| 强模糊 | `--glass-blur-strong` | `blur(30px)` |

### 3.2 玻璃卡片规范

- 所有卡片使用 `backdrop-filter: var(--glass-blur)`
- 卡片顶部 1px 白色渐变高光线（模拟边缘折射）
- hover 时卡片上浮 2-4px + 阴影增强 + 液态高光出现
- 边框使用半透明白色 (`--glass-border`)

---

## 四、字体

| 层级 | 字体族 | 变体 | 大小 |
|------|--------|------|------|
| 系统默认 | `--font-sans` | `"SF Pro Display", "PingFang SC", "Noto Sans SC", -apple-system, sans-serif` | 14px body |
| 等宽 | `--font-mono` | `"SF Mono", "Fira Code", "Cascadia Code", monospace` | - |

- 页面标题 28px weight 600
- 卡片标题 16px weight 600
- 正文 14px weight 400
- 标签/辅助文字 12-13px weight 500

---

## 五、圆角与阴影

### 5.1 圆角

| 级别 | 变量 | 值 |
|------|------|-----|
| 大圆角（卡片/弹窗） | `--radius-lg` | `28px` |
| 标准圆角（卡片） | `--radius` | `24px` |
| 小圆角（按钮/输入框） | `--radius-sm` | `14px` |
| 极小圆角（分页/标签） | `--radius-xs` | `10px` |

### 5.2 阴影（蓝色调）

| 级别 | 变量 | 值 |
|------|------|------|
| 标准 | `--shadow` | `0 4px 20px rgba(120,160,255,0.10), 0 1px 3px rgba(91,140,255,0.06)` |
| 大 | `--shadow-lg` | `0 12px 40px rgba(120,160,255,0.14), 0 4px 12px rgba(91,140,255,0.08)` |
| 抬起 | `--shadow-raised` | `0 8px 32px rgba(120,160,255,0.16)` |
| 发光 | `--shadow-glow` | `0 0 40px rgba(91,140,255,0.15), 0 0 80px rgba(139,124,255,0.08)` |

---

## 六、动画

| 动画 | 时长 | 缓动 | 说明 |
|------|------|------|------|
| 页面进入 | 500ms | cubic-bezier(.25,.1,.25,1) | fadeInUp 从下向上浮现 |
| 子元素 stagger | 0-150ms | 同上 | 依次延迟入场 |
| 卡片 hover | 300-400ms | 同上 | 上浮 + 阴影 + 高光 |
| 模态框进入 | 350ms | 同上 | scale(0.96→1) + fade |
| Toast 滑入 | 350ms | 同上 | 从右侧滑入 |
| 背景光晕 | 20s | ease-in-out | bgFlow 缓慢位移 |
| 侧边栏高光 | 1.5s | ease-in-out | liquidShimmer 扫描 |
| 按钮按下 | 100ms | - | scale(0.98) |

所有过渡使用 `cubic-bezier(0.25, 0.1, 0.25, 1)`。

---

## 七、布局结构

```
┌──────────────────────────────────────────────────┐
│  .navbar (60px) — 漂浮玻璃条                      │
│  backdrop-blur: 30px · position: sticky           │
├────────┬─────────────────────────────────────────┤
│.sidebar│  .main-content                          │
│240px   │  padding: 28px 32px                     │
│玻璃毛   │                                         │
│玻璃背景 │  卡片区域                                │
│blur:   │  glass cards                            │
│30px    │                                         │
└────────┴─────────────────────────────────────────┘
```

- 整体背景：`body::before` 伪元素，5 层径向渐变光晕，20s 流动动画
- 侧边栏底部有 1px 白色渐变顶线（高光）

---

## 八、组件速查

### 8.1 按钮

```html
<button class="btn btn-primary">主操作</button>    <!-- 蓝紫渐变 -->
<button class="btn btn-success">通过</button>       <!-- 绿色渐变 -->
<button class="btn btn-danger">删除</button>        <!-- 红色渐变 -->
<button class="btn btn-warning">警告</button>       <!-- 橙色渐变 -->
<button class="btn btn-outline">取消</button>       <!-- 玻璃边框 -->
<button class="btn btn-primary btn-sm">小按钮</button>
```

### 8.2 模态框

```html
<div class="modal-overlay" id="xxx-modal">
  <div class="modal">
    <div class="modal-header"><h3>标题</h3></div>
    <div class="modal-body">内容</div>
    <div class="modal-footer">按钮</div>
  </div>
</div>
```

JS: `openModal('xxx-modal')` / `closeModal('xxx-modal')`

### 8.3 表格

```html
<table class="table">...</table>
```

状态标签: `<span class="status-badge available">可用</span>`

### 8.4 单据分组

```html
<div class="doc-group">
  <div class="doc-group-header">...</div>
  <div class="doc-group-body">...</div>
</div>
```

---

## 九、硬约束

- **禁止** `confirm()` / `prompt()` / `alert()` — 使用自定义模态框
- **禁止** 外部 CDN 引用 — 所有资源本地托管
- **禁止** 内联 style 硬编码颜色 — 使用 CSS 变量
- **禁止** emoji 作为图标 — 使用 Bootstrap Icons
- **设计风格固定** — 本项目使用 Apple Liquid Glass，不混入其他风格

---

## 十、CSS 文件位置

| 文件 | 用途 |
|------|------|
| `frontend/static/css/style.css` | 主设计系统（~580行） |
| `frontend/static/css/login.css` | 登录页（主样式在 style.css） |
| `frontend/static/css/bootstrap-icons.css` | 图标库 |
