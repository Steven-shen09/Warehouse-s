# 设计系统更新：Apple Liquid Glass → Cursor Warm Minimal

> 日期：2026-05-22
> 状态：已确认
> 来源：`nexu-io/open-design` → `design-systems/cursor/DESIGN.md`

---

## 一、动机

将 Warehouse-s 的 Apple VisionOS Liquid Glass（蓝紫冷调玻璃拟态）完整替换为 Cursor Warm Minimal（暖色极简平面风），参考 `Cursor-showcase.html` 的设计语言。

## 二、色彩系统

### 2.1 核心色

| 角色 | 变量名 | 值 |
|------|--------|-----|
| 页面背景 | `--bg` | `#F2F1ED` |
| 次级背景 | `--bg-soft` | `#E6E5E0` |
| 主文字 | `--text` | `#26251E` |
| 标题文字 | `--text-title` | `#26251E` |
| 次级文字 | `--text-secondary` | `rgba(38,37,30,0.56)` |
| 辅助文字 | `--text-muted` | `rgba(38,37,30,0.40)` |
| 主色（品牌橙） | `--primary` | `#F54E00` |
| 点缀色（金） | `--accent` | `#C08532` |

### 2.2 功能色

| 用途 | 变量 | 值 |
|------|------|-----|
| 成功 | `--success` | `#1F8A65` |
| 警告 | `--warning` | `#C08532` |
| 危险 | `--danger` | `#CF2D56` |
| 信息 | `--info` | `#9FBBE0` |

### 2.3 表面色（替换玻璃透明背景）

| 用途 | 变量 | 值 |
|------|------|-----|
| 卡片背景 | `--bg-card` | `#E6E5E0` |
| 卡片悬停 | `--bg-card-hover` | `#EBEAE5` |
| 侧边栏 | `--bg-sidebar` | `#E6E5E0` |
| 顶部导航 | `--bg-header` | `#F2F1ED` |
| 输入框背景 | `--input-bg` | `#FFFFFF` |
| 表格交替行 | - | `#F7F7F4` / `#F2F1ED` |

### 2.4 边框（oklab 暖棕空间）

| 用途 | 变量 | 值 |
|------|------|-----|
| 标准边框 | `--border` | `oklab(0.263084 -0.00230259 0.0124794 / 0.1)` |
| 强调边框 | `--border-strong` | `oklab(0.263084 -0.00230259 0.0124794 / 0.2)` |
| 重边框 | `--border-heavy` | `rgba(38,37,30,0.55)` |

### 2.5 状态标签色

| 状态 | 变量 | 值 |
|------|------|-----|
| 可用 | `--status-available` | `#1F8A65` |
| 已租借 | `--status-lent` | `#9FBBE0` |
| 损坏 | `--status-damaged` | `#CF2D56` |
| 待审核 | `--status-pending` | `#C08532` |
| 已通过 | `--status-approved` | `#9FC9A2` |
| 已驳回 | `--status-rejected` | `#CF2D56` |
| 已归还 | `--status-returned` | `#C0A8DD` |
| 逾期 | `--status-overdue` | `#F54E00` |

---

## 三、字体系统

| 层级 | 元素 | 字号 | 字重 | 说明 |
|------|------|------|------|------|
| 页面大标题 | `.main-content h2` | 44px | 700 | letter-spacing: -0.02em |
| 数据数字 | `.stat-value` | 42px | 700 | 纯色 `#26251E`，无渐变 |
| 区块标题 | `.card-title` | 20px | 600 | — |
| 按钮 | `.btn` | 14.5px | 500 | — |
| 表格正文 | `.table` | 14px | 500 | — |
| 侧边栏 | `.sidebar a` | 13px | 500 | — |
| 卡片标签 | `.stat-label` | 13px | 500 | — |
| 状态标签 | `.status-badge` | 12px | 600 | — |
| 次级文字 | - | 13px | 400 | — |

### 字体栈

```css
--font-sans: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
--font-mono: ui-monospace, 'SF Mono', 'Cascadia Code', monospace;
```

---

## 四、圆角

| 级别 | 变量 | 值 |
|------|------|-----|
| 大圆角 | `--radius-lg` | `24px` |
| 标准 | `--radius` | `14px` |
| 小圆角 | `--radius-sm` | `10px` |
| 极小 | `--radius-xs` | `8px` |

---

## 五、阴影

**不再使用多层阴影和内发光。** 仅在 hover 时使用轻微上浮：

```css
--shadow-hover: 0 2px 16px rgba(38,37,30,0.06);
```

卡片/侧边栏/导航栏均无默认阴影，层次靠色彩差区分。

---

## 六、按钮系统

| 按钮 | 背景 | 文字颜色 | 边框 |
|------|------|---------|------|
| `.btn-primary` | `#F54E00` | `#FFFFFF` | 无 |
| `.btn-success` | `#1F8A65` | `#FFFFFF` | 无 |
| `.btn-danger` | `#CF2D56` | `#FFFFFF` | 无 |
| `.btn-warning` | `#C08532` | `#FFFFFF` | 无 |
| `.btn-outline` | 透明 | `#26251E` | `1px oklab 20%` |
| `.btn-sm` | 同色 | 同色 | 字号 12px |

Hover：`filter: brightness(1.06)` + `translateY(-1px)`，无扫光动画。

---

## 七、组件适配

### 7.1 导航栏
- 实色背景 `#F2F1ED`，底部 1px 暖棕边框
- 移除 `backdrop-filter: blur(24px)` 和半透明背景

### 7.2 侧边栏
- 实色背景 `#E6E5E0`，移除 `backdrop-filter: blur(30px)`
- 激活项：白色背景 + 1px 边框

### 7.3 卡片
- 实色背景 `#E6E5E0`，14px 圆角
- 无阴影，hover 轻微上浮 2px

### 7.4 表格
- 交替行背景：`#F7F7F4` / `#F2F1ED`
- 移除透明行背景

### 7.5 模态框
- 纯白背景 `#FFFFFF` + 1px 暖棕边框
- 移除 `backdrop-filter: blur(40px)` 和 `rgba(255,255,255,0.80)` 半透明
- 遮罩：`rgba(38,37,30,0.20)`

### 7.6 空状态
- 保留 Bootstrap Icons 矢量图标
- 文案颜色 `--text-muted`

### 7.7 状态标签
- pill 形状（`border-radius: 999px`）
- 背景：对应状态色的 12% 透明度
- 文字：对应状态色实色

---

## 八、将被删除的内容

以下 Liquid Glass 特性将全部移除：

1. 5 层径向渐变背景光晕 + 20s 流动动画 (`body::before`)
2. SVG `feTurbulence` 噪点纹理 (`body::after`)
3. 多层 `backdrop-filter: blur()`（导航栏 24px、侧边栏 30px、卡片 16px、模态框 40px）
4. `mask-composite: exclude` 折射高光边框
5. `skewX(-20deg)` 液态扫光动画
6. 蓝色调 `inset` 阴影（`inset 0 1px 0`）
7. 所有蓝紫渐变文字（`linear-gradient(135deg, #5B8CFF, #8B7CFF)`）

---

## 九、不改动的内容

- HTML 结构（侧边栏/卡片/表格/模态框/文档分组）
- HTMX 2.0 + Alpine.js 3.14 交互逻辑
- Bootstrap Icons 图标
- Jinja2 模板继承结构
- 响应式布局断点
- 无暗色模式（用户确认不需要）

---

## 十、实施范围

| 文件 | 操作 |
|------|------|
| `frontend/static/css/style.css` | 完整重写 `:root` + 组件样式 |
| `frontend/static/css/login.css` | 适配新色彩变量 |
| `design-system/MASTER.md` | 更新为 Cursor Warm 设计规范 |
| `CLAUDE.md` / `AGENTS.md` | 更新设计系统描述 |
