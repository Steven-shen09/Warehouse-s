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
