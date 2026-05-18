# 物品批量导入功能 — 实施计划

> **对于 agentic workers：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 按任务逐步实现。步骤使用 checkbox (`- [ ]`) 语法跟踪。

**目标：** 在物品管理页面添加 CSV/Excel 批量导入功能，支持预览、同名检测、累加更新。

**架构：** 后端新增 3 个 API 端点（preview/confirm/template），前端在 items.html 新增三步导入模态框。文件解析在后端统一处理，前端仅负责上传和展示。

**技术栈：** Python FastAPI + SQLite, Jinja2 + HTMX + Alpine.js, openpyxl

---

## 文件结构

| 文件 | 职责 | 变更类型 |
|------|------|---------|
| `app/schemas/item.py` | 导入相关的 Pydantic schema（ImportPreviewRow, ImportConfirmRequest） | 修改 |
| `app/api/items.py` | 3 个新端点：preview / confirm / template，文件解析函数 | 修改 |
| `frontend/templates/pages/items.html` | 导入按钮 + 三步模态框 + JS 逻辑 | 修改 |
| `requirements.txt` | 新增 openpyxl 依赖 | 修改 |

---

### Task 1: 添加 openpyxl 依赖

**文件：**
- 修改：`requirements.txt`

- [ ] **Step 1: 在 requirements.txt 中添加 openpyxl**

在文件末尾添加一行：

```
openpyxl==3.1.5
```

- [ ] **Step 2: 安装依赖**

```bash
pip install openpyxl==3.1.5
```

- [ ] **Step 3: 提交**

```bash
git add requirements.txt
git commit -m "deps: 添加 openpyxl 依赖用于 Excel 文件解析"
```

---

### Task 2: 添加导入相关 Schema

**文件：**
- 修改：`app/schemas/item.py`

- [ ] **Step 1: 在 item.py 末尾添加 ImportPreviewRow 和 ImportConfirmRequest schema**

```python
# ── 批量导入 Schema ──

class ImportPreviewRow(BaseModel):
    """导入预览单行"""
    index: int
    data: dict
    status: str  # "ok" | "duplicate" | "error"
    message: Optional[str] = None
    duplicate_item: Optional[dict] = None


class ImportConfirmRow(BaseModel):
    """确认导入单行选择"""
    index: int
    action: str  # "create" | "add_to_existing"
    item_id: Optional[int] = None  # 仅 add_to_existing 时需要


class ImportConfirmRequest(BaseModel):
    """确认导入请求"""
    rows: list[ImportConfirmRow]


class ImportResult(BaseModel):
    """导入结果"""
    message: str
    imported: int
    updated: int
    skipped: int
```

注意：需在文件顶部添加 `from typing import Optional`（检查是否已存在，若已存在则无需添加）。

- [ ] **Step 2: 验证 schema 导入正确**

```bash
cd C:\Users\slama\first-cc\Warehouse-s && python -c "from app.schemas.item import ImportPreviewRow, ImportConfirmRow, ImportConfirmRequest, ImportResult; print('OK')"
```

期望输出：`OK`

- [ ] **Step 3: 提交**

```bash
git add app/schemas/item.py
git commit -m "feat: 添加批量导入相关 Pydantic schema"
```

---

### Task 3: 添加后端 API 端点

**文件：**
- 修改：`app/api/items.py`

需要在文件顶部添加新导入，然后添加 3 个端点 + 2 个辅助函数。

- [ ] **Step 1: 在 items.py 顶部添加新导入**

在现有 import 后添加：

```python
import csv
import io
import os
from fastapi import UploadFile, File, Query, Response
from app.schemas.item import ImportPreviewRow, ImportConfirmRow, ImportConfirmRequest, ImportResult
```

注意：`from fastapi import ...` 行需要合并到已有的 fastapi import 中。检查现有第 2 行：
```python
from fastapi import APIRouter, Depends, HTTPException
```
改为：
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response
```

- [ ] **Step 2: 添加文件解析辅助函数**

在 `router = APIRouter(...)` 之后、第一个路由之前添加：

```python
# ── 导入模板列名映射 ──
IMPORT_COLUMNS = ["物品名称", "分类", "描述", "存放位置", "总数量", "单价(元)", "预警阈值"]


def parse_uploaded_file(file_content: bytes, filename: str) -> list[dict]:
    """解析上传的 CSV/Excel 文件，返回行数据列表（每行一个 dict）"""
    rows = []
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".csv":
        content = io.StringIO(file_content.decode("utf-8-sig"))
        reader = csv.DictReader(content)
        for row in reader:
            rows.append(row)
    elif ext in (".xlsx", ".xls"):
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(file_content), read_only=True)
        ws = wb.active
        headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if all(v is None for v in row):
                continue
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = str(row[i]) if row[i] is not None else ""
            rows.append(row_dict)
        wb.close()
    else:
        raise HTTPException(status_code=400, detail="不支持的文件格式，请上传 CSV 或 Excel 文件")

    return rows


def validate_and_check_duplicates(conn, rows: list[dict]) -> list[dict]:
    """逐行验证并检查同名重复，返回预览行列表"""
    result = []
    for i, row in enumerate(rows):
        name = row.get("物品名称", "").strip()
        index = i + 1

        # 验证名称
        if not name:
            result.append({
                "index": index,
                "data": row,
                "status": "error",
                "message": "物品名称不能为空",
                "duplicate_item": None,
            })
            continue
        if len(name) > 100:
            result.append({
                "index": index,
                "data": row,
                "status": "error",
                "message": f"物品名称不能超过100字符（当前{len(name)}字符）",
                "duplicate_item": None,
            })
            continue

        # 验证数量
        qty_str = row.get("总数量", "1").strip()
        try:
            qty = int(qty_str) if qty_str else 1
            if qty < 1:
                raise ValueError
        except ValueError:
            result.append({
                "index": index,
                "data": row,
                "status": "error",
                "message": f"总数量必须为大于等于1的整数（当前值：{qty_str}）",
                "duplicate_item": None,
            })
            continue

        # 验证单价
        value_str = row.get("单价(元)", "0").strip()
        try:
            value = float(value_str) if value_str else 0.0
            if value < 0:
                raise ValueError
        except ValueError:
            result.append({
                "index": index,
                "data": row,
                "status": "error",
                "message": f"单价必须为非负数字（当前值：{value_str}）",
                "duplicate_item": None,
            })
            continue

        # 验证预警阈值
        threshold_str = row.get("预警阈值", "2").strip()
        try:
            threshold = int(threshold_str) if threshold_str else 2
            if threshold < 0:
                raise ValueError
        except ValueError:
            result.append({
                "index": index,
                "data": row,
                "status": "error",
                "message": f"预警阈值必须为非负整数（当前值：{threshold_str}）",
                "duplicate_item": None,
            })
            continue

        # 检查同名重复
        existing = conn.execute(
            "SELECT id, name, total_quantity FROM items WHERE name = ?", (name,)
        ).fetchone()

        if existing:
            result.append({
                "index": index,
                "data": row,
                "status": "duplicate",
                "message": f"同名物品已存在（ID:{existing['id']}，现有库存:{existing['total_quantity']}），勾选后累加",
                "duplicate_item": {"id": existing["id"], "name": existing["name"], "total_quantity": existing["total_quantity"]},
            })
        else:
            result.append({
                "index": index,
                "data": row,
                "status": "ok",
                "message": None,
                "duplicate_item": None,
            })

    return result
```

- [ ] **Step 3: 添加 POST /import/preview 端点**

在文件末尾（`mark_available` 端点之后）添加：

```python
@router.post("/import/preview")
def import_preview(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """上传文件并预览解析结果（不写入数据库）"""
    # 验证文件类型
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(status_code=400, detail="仅支持 CSV (.csv) 和 Excel (.xlsx) 文件")

    # 验证文件大小（最大 5MB）
    file_content = file.file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")

    # 解析文件
    try:
        rows = parse_uploaded_file(file_content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败：{str(e)}")

    if not rows:
        raise HTTPException(status_code=400, detail="文件中没有数据行")

    if len(rows) > 500:
        raise HTTPException(status_code=400, detail="单次导入最多 500 行")

    # 验证并检查重复
    preview_rows = validate_and_check_duplicates(conn, rows)

    # 统计
    summary = {
        "total": len(preview_rows),
        "ok": sum(1 for r in preview_rows if r["status"] == "ok"),
        "duplicate": sum(1 for r in preview_rows if r["status"] == "duplicate"),
        "error": sum(1 for r in preview_rows if r["status"] == "error"),
    }

    return {"rows": preview_rows, "summary": summary}
```

- [ ] **Step 4: 添加 POST /import/confirm 端点**

```python
@router.post("/import/confirm")
def import_confirm(
    file: UploadFile = File(...),
    selections: str = Form(default=""),
    current_user: dict = Depends(require_role("admin", "approver")),
    conn=Depends(get_db),
):
    """确认导入（事务保护，全部或全不）"""
    import json

    try:
        selected_rows = json.loads(selections)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="选择数据格式错误")

    if not selected_rows:
        raise HTTPException(status_code=400, detail="没有选择任何行")

    # 重新解析文件
    file_content = file.file.read()
    try:
        rows = parse_uploaded_file(file_content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败：{str(e)}")

    # 重新验证
    preview_rows = validate_and_check_duplicates(conn, rows)
    errors = [r for r in preview_rows if r["status"] == "error"]
    if errors:
        error_msgs = "; ".join(f"第{r['index']}行: {r['message']}" for r in errors)
        raise HTTPException(status_code=400, detail=f"数据验证失败：{error_msgs}")

    # 构建选择的行索引查找
    selection_map = {s["index"]: s for s in selected_rows}

    imported = 0
    updated = 0

    try:
        conn.execute("BEGIN IMMEDIATE")

        for row_data in preview_rows:
            idx = row_data["index"]
            if idx not in selection_map:
                continue  # 跳过未勾选的行

            sel = selection_map[idx]
            data = row_data["data"]
            name = data.get("物品名称", "").strip()
            category = data.get("分类", "").strip()
            description = data.get("描述", "").strip()
            location = data.get("存放位置", "").strip()
            total_quantity = int(data.get("总数量", "1").strip() or "1")
            value = float(data.get("单价(元)", "0").strip() or "0")
            low_stock_threshold = int(data.get("预警阈值", "2").strip() or "2")

            if sel.get("action") == "add_to_existing" and sel.get("item_id"):
                # 累加到已有物品
                conn.execute(
                    "UPDATE items SET total_quantity = total_quantity + ?, updated_at = datetime('now','localtime') WHERE id = ?",
                    (total_quantity, sel["item_id"]),
                )
                updated += 1
            else:
                # 创建新物品
                conn.execute(
                    """INSERT INTO items (name, category, description, location, total_quantity, value, low_stock_threshold)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (name, category, description, location, total_quantity, value, low_stock_threshold),
                )
                imported += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="导入失败，已回滚所有更改")

    skipped = len(preview_rows) - imported - updated

    return ImportResult(
        message=f"成功导入 {imported} 件物品，累加更新 {updated} 件物品",
        imported=imported,
        updated=updated,
        skipped=skipped,
    )
```

- [ ] **Step 5: 添加 GET /import/template 端点**

```python
@router.get("/import/template")
def download_template(
    fmt: str = Query("csv", alias="format"),
    current_user: dict = Depends(get_current_user),
):
    """下载导入模板文件"""
    if fmt == "xlsx":
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "物品导入模板"
        ws.append(IMPORT_COLUMNS)
        # 添加示例行
        ws.append(["示例：笔记本电脑", "电子设备", "ThinkPad X1", "A-101", "5", "4500", "2"])
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=import_template.xlsx"},
        )
    else:
        # 默认 CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(IMPORT_COLUMNS)
        content = output.getvalue()
        # 添加 BOM 以便 Excel 正确识别 UTF-8
        return Response(
            content="﻿" + content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=import_template.csv"},
        )
```

- [ ] **Step 6: 验证后端端点可导入**

```bash
cd C:\Users\slama\first-cc\Warehouse-s && python -c "from app.api.items import router; print('OK')"
```

期望输出：`OK`

- [ ] **Step 7: 提交**

```bash
git add app/api/items.py
git commit -m "feat: 添加批量导入 API 端点（preview/confirm/template）"
```

---

### Task 4: 添加前端 UI — 导入模态框 HTML

**文件：**
- 修改：`frontend/templates/pages/items.html`

- [ ] **Step 1: 在筛选栏右侧添加"导入物品"按钮**

将 items.html 第 4-14 行的内容区域开头改为：

```html
<div class="flex-between mb-16">
  <h2>物品管理</h2>
  {% if current_user.role in ('admin', 'approver') %}
  <div style="display:flex;gap:8px;">
    <button class="btn btn-outline" onclick="openImportModal()">
      <i class="bi bi-upload"></i> 导入物品
    </button>
    <button class="btn btn-primary" onclick="openModal('item-form-modal')">
      <i class="bi bi-plus-lg"></i> 新增物品
    </button>
  </div>
  {% endif %}
</div>
```

- [ ] **Step 2: 在页面末尾（`{% endblock %}` 之前）添加导入模态框 HTML**

在 `{% endblock %}`（第 157 行）之前，即 `<!-- 批量提交租借清单模态框 -->` 的 `</div>` 之后插入：

```html
<!-- 导入物品模态框 -->
<div class="modal-overlay" id="import-modal">
  <div class="modal" style="max-width:800px;">
    <div class="modal-header">
      <h3>导入物品</h3>
      <button class="btn btn-sm btn-outline" onclick="closeImportModal()">&times;</button>
    </div>
    <div class="modal-body">
      <!-- 步骤指示器 -->
      <div class="import-steps" id="import-steps">
        <div class="import-step active" data-step="1">
          <span class="import-step-num">1</span>
          <span class="import-step-label">选择文件</span>
        </div>
        <div class="import-step-connector"></div>
        <div class="import-step" data-step="2">
          <span class="import-step-num">2</span>
          <span class="import-step-label">预览确认</span>
        </div>
        <div class="import-step-connector"></div>
        <div class="import-step" data-step="3">
          <span class="import-step-num">3</span>
          <span class="import-step-label">完成</span>
        </div>
      </div>

      <!-- 步骤 1：选择文件 -->
      <div id="import-step1-content">
        <div class="import-dropzone" id="import-dropzone" onclick="document.getElementById('import-file-input').click()">
          <div class="import-dropzone-icon">📁</div>
          <p>拖拽文件到此处，或点击选择文件</p>
          <p class="text-muted" style="font-size:13px;">支持 CSV (.csv) / Excel (.xlsx) 格式，最大 5MB</p>
          <input type="file" id="import-file-input" accept=".csv,.xlsx,.xls" style="display:none;" onchange="handleFileSelected(this.files[0])">
        </div>
        <div id="import-selected-file" style="display:none;margin-top:12px;">
          <span id="import-selected-filename"></span>
          <button class="btn btn-sm btn-outline" onclick="resetImportStep1()">重新选择</button>
        </div>
        <div style="margin-top:12px;">
          <a href="javascript:void(0)" onclick="downloadTemplate('csv')" class="text-muted" style="font-size:13px;">📥 下载导入模板 (CSV)</a>
          <span style="margin:0 8px;color:var(--text-secondary);">|</span>
          <a href="javascript:void(0)" onclick="downloadTemplate('xlsx')" class="text-muted" style="font-size:13px;">📥 下载导入模板 (Excel)</a>
        </div>
        <div style="margin-top:16px;display:flex;justify-content:flex-end;gap:8px;">
          <button class="btn btn-outline" onclick="closeImportModal()">取消</button>
          <button class="btn btn-primary" id="import-upload-btn" disabled onclick="uploadFileForPreview()">上传并预览</button>
        </div>
      </div>

      <!-- 步骤 2：预览确认 -->
      <div id="import-step2-content" style="display:none;">
        <div id="import-preview-summary" class="mb-16"></div>
        <div class="import-preview-table-wrapper" style="max-height:360px;overflow:auto;">
          <table class="table" id="import-preview-table">
            <thead><tr>
              <th class="col-check">选择</th>
              <th>#</th>
              <th>物品名称</th>
              <th>分类</th>
              <th>总数量</th>
              <th>单价</th>
              <th>状态</th>
            </tr></thead>
            <tbody></tbody>
          </table>
        </div>
        <div style="margin-top:12px;display:flex;align-items:center;gap:8px;">
          <label style="font-size:14px;cursor:pointer;">
            <input type="checkbox" id="import-select-all" onchange="toggleAllImportRows()" checked> 全选/取消
          </label>
        </div>
        <div style="margin-top:16px;display:flex;justify-content:flex-end;gap:8px;">
          <button class="btn btn-outline" onclick="resetImportStep1()">重新上传</button>
          <button class="btn btn-outline" onclick="closeImportModal()">取消</button>
          <button class="btn btn-primary" id="import-confirm-btn" onclick="confirmImport()">确认导入</button>
        </div>
      </div>

      <!-- 步骤 3：完成 -->
      <div id="import-step3-content" style="display:none;text-align:center;padding:32px 0;">
        <div id="import-result-icon" style="font-size:48px;margin-bottom:16px;"></div>
        <h4 id="import-result-message" style="margin-bottom:16px;"></h4>
        <div id="import-result-detail" class="text-muted" style="margin-bottom:24px;"></div>
        <button class="btn btn-primary" onclick="finishImport()">关闭</button>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 3: 添加导入步骤指示器的 CSS 样式**

在 `{% block scripts %}` 之前添加一个内联 `<style>` 块：

```html
<style>
.import-steps { display:flex; align-items:center; justify-content:center; margin-bottom:24px; }
.import-step { display:flex; flex-direction:column; align-items:center; gap:4px; opacity:0.4; }
.import-step.active { opacity:1; }
.import-step-num { width:28px; height:28px; border-radius:50%; background:var(--primary); color:#fff; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700; }
.import-step-label { font-size:12px; color:var(--text-secondary); }
.import-step-connector { width:48px; height:2px; background:var(--border-color, rgba(128,128,128,.2)); margin:0 8px; margin-bottom:16px; }
.import-dropzone { border:2px dashed var(--border-color, rgba(128,128,128,.3)); border-radius:var(--radius); padding:32px; text-align:center; cursor:pointer; transition:all .2s; }
.import-dropzone:hover, .import-dropzone.drag-over { border-color:var(--primary); background:rgba(91,140,255,.06); }
.import-preview-table-wrapper { border-radius:var(--radius); border:1px solid var(--border-color, rgba(128,128,128,.15)); }
.import-row-duplicate { background:rgba(255,193,7,.08); }
.import-row-error { background:rgba(255,59,48,.08); }
</style>
```

- [ ] **Step 4: 提交**

```bash
git add frontend/templates/pages/items.html
git commit -m "feat: 添加导入模态框 HTML 结构和样式"
```

---

### Task 5: 添加前端 JS 导入逻辑

**文件：**
- 修改：`frontend/templates/pages/items.html`（在 `<script>` 标签内添加）

- [ ] **Step 1: 添加导入相关 JS 变量和函数**

在 `<script>` 标签内（`currentPage` 变量之后）添加：

```javascript
// ── 导入功能 ──
let importPreviewData = null;
let importSelectedFile = null;

function openImportModal() {
  importPreviewData = null;
  importSelectedFile = null;
  resetImportStep1();
  document.getElementById('import-file-input').value = '';
  showImportStep(1);
  openModal('import-modal');
}

function closeImportModal() {
  closeModal('import-modal');
}

function resetImportStep1() {
  importPreviewData = null;
  importSelectedFile = null;
  document.getElementById('import-file-input').value = '';
  document.getElementById('import-selected-file').style.display = 'none';
  document.getElementById('import-upload-btn').disabled = true;
  document.getElementById('import-dropzone').style.display = '';
  showImportStep(1);
}

function showImportStep(step) {
  document.getElementById('import-step1-content').style.display = step === 1 ? '' : 'none';
  document.getElementById('import-step2-content').style.display = step === 2 ? '' : 'none';
  document.getElementById('import-step3-content').style.display = step === 3 ? '' : 'none';

  document.querySelectorAll('#import-steps .import-step').forEach(el => {
    el.classList.toggle('active', parseInt(el.dataset.step) <= step);
  });
}

function handleFileSelected(file) {
  if (!file) return;
  importSelectedFile = file;
  document.getElementById('import-selected-filename').textContent = file.name;
  document.getElementById('import-selected-file').style.display = '';
  document.getElementById('import-dropzone').style.display = 'none';
  document.getElementById('import-upload-btn').disabled = false;
}

// 拖拽支持
(function initDropzone() {
  document.addEventListener('DOMContentLoaded', () => {
    const dz = document.getElementById('import-dropzone');
    if (!dz) return;
    dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('drag-over'); });
    dz.addEventListener('dragleave', () => { dz.classList.remove('drag-over'); });
    dz.addEventListener('drop', (e) => {
      e.preventDefault();
      dz.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file) {
        document.getElementById('import-file-input').files = e.dataTransfer.files;
        handleFileSelected(file);
      }
    });
  });
})();

async function uploadFileForPreview() {
  if (!importSelectedFile) return;

  const btn = document.getElementById('import-upload-btn');
  btn.disabled = true;
  btn.textContent = '解析中...';

  const formData = new FormData();
  formData.append('file', importSelectedFile);

  const resp = await fetch('/api/v1/items/import/preview', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${AppState.token}` },
    body: formData,
  });

  btn.disabled = false;
  btn.textContent = '上传并预览';

  if (!resp.ok) {
    const err = await resp.json();
    showToast(err.detail || '文件解析失败', 'error');
    return;
  }

  importPreviewData = await resp.json();
  renderImportPreview();
  showImportStep(2);
}

function renderImportPreview() {
  const data = importPreviewData;
  if (!data) return;

  // 摘要
  const s = data.summary;
  document.getElementById('import-preview-summary').innerHTML =
    `解析结果：共 <strong>${s.total}</strong> 行，` +
    `<span style="color:#34C759;">✅ ${s.ok} 条可导入</span>` +
    (s.duplicate > 0 ? `，<span style="color:#FF9500;">⚠ ${s.duplicate} 条同名重复</span>` : '') +
    (s.error > 0 ? `，<span style="color:#FF3B30;">❌ ${s.error} 条错误</span>` : '');

  // 表格
  const tbody = document.querySelector('#import-preview-table tbody');
  tbody.innerHTML = data.rows.map(row => {
    const checked = row.status === 'ok' ? 'checked' : '';
    const disabled = row.status === 'error' ? 'disabled' : '';
    const rowClass = row.status === 'duplicate' ? 'import-row-duplicate' : (row.status === 'error' ? 'import-row-error' : '');
    const statusHtml = row.status === 'ok'
      ? '<span class="status-badge available">正常</span>'
      : row.status === 'duplicate'
        ? `<span class="status-badge lent" title="${escapeHtml(row.message)}">⚠ 重复</span><br><small class="text-muted">${escapeHtml(row.message)}</small>`
        : `<span class="status-badge damaged" title="${escapeHtml(row.message)}">❌ 错误</span><br><small style="color:#FF3B30;">${escapeHtml(row.message)}</small>`;

    return `
      <tr class="${rowClass}">
        <td class="col-check">
          <input type="checkbox" class="import-row-checkbox" data-index="${row.index}"
            data-action="${row.status === 'duplicate' ? 'add_to_existing' : 'create'}"
            data-item-id="${row.duplicate_item ? row.duplicate_item.id : ''}"
            ${checked} ${disabled} onchange="onImportRowToggle()">
        </td>
        <td>${row.index}</td>
        <td>${escapeHtml(row.data['物品名称'] || '')}</td>
        <td>${escapeHtml(row.data['分类'] || '')}</td>
        <td>${escapeHtml(row.data['总数量'] || '1')}</td>
        <td>${escapeHtml(row.data['单价(元)'] || '0')}</td>
        <td>${statusHtml}</td>
      </tr>
    `;
  }).join('');

  document.getElementById('import-select-all').checked = true;
}

function onImportRowToggle() {
  const allCbs = document.querySelectorAll('.import-row-checkbox:not([disabled])');
  const checkedCbs = document.querySelectorAll('.import-row-checkbox:not([disabled]):checked');
  document.getElementById('import-select-all').checked = allCbs.length === checkedCbs.length;
}

function toggleAllImportRows() {
  const selectAll = document.getElementById('import-select-all').checked;
  document.querySelectorAll('.import-row-checkbox:not([disabled])').forEach(cb => {
    cb.checked = selectAll;
  });
}

async function confirmImport() {
  const checkedRows = document.querySelectorAll('.import-row-checkbox:checked');
  if (checkedRows.length === 0) {
    showToast('请至少选择一行', 'warning');
    return;
  }

  const selections = [];
  checkedRows.forEach(cb => {
    const sel = { index: parseInt(cb.dataset.index), action: cb.dataset.action };
    if (cb.dataset.action === 'add_to_existing' && cb.dataset.itemId) {
      sel.item_id = parseInt(cb.dataset.itemId);
    }
    selections.push(sel);
  });

  const btn = document.getElementById('import-confirm-btn');
  btn.disabled = true;
  btn.textContent = '导入中...';

  const formData = new FormData();
  formData.append('file', importSelectedFile);
  formData.append('selections', JSON.stringify(selections));

  const resp = await fetch('/api/v1/items/import/confirm', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${AppState.token}` },
    body: formData,
  });

  btn.disabled = false;
  btn.textContent = '确认导入';

  if (!resp.ok) {
    const err = await resp.json();
    document.getElementById('import-result-icon').textContent = '❌';
    document.getElementById('import-result-message').textContent = '导入失败';
    document.getElementById('import-result-detail').textContent = err.detail || '未知错误';
    showImportStep(3);
    return;
  }

  const result = await resp.json();
  document.getElementById('import-result-icon').textContent = '✅';
  document.getElementById('import-result-message').textContent = '导入成功！';
  document.getElementById('import-result-detail').innerHTML =
    `成功导入 <strong>${result.imported}</strong> 件物品` +
    (result.updated > 0 ? `，累加更新 <strong>${result.updated}</strong> 件物品` : '') +
    (result.skipped > 0 ? `，跳过 <strong>${result.skipped}</strong> 条` : '');
  showImportStep(3);
}

function finishImport() {
  closeImportModal();
  loadItems(currentPage);
}

function downloadTemplate(format) {
  const url = `/api/v1/items/import/template?format=${format}`;
  const a = document.createElement('a');
  a.href = url;
  a.download = format === 'xlsx' ? 'import_template.xlsx' : 'import_template.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/templates/pages/items.html
git commit -m "feat: 添加导入功能前端 JS 逻辑"
```

---

### Task 6: 端到端验证

- [ ] **Step 1: 启动后端服务验证无导入错误**

```bash
cd C:\Users\slama\first-cc\Warehouse-s && python -c "from app import create_app; app = create_app(); print('App created successfully')"
```

期望输出：`App created successfully`

- [ ] **Step 2: 运行已有测试确保无回归**

```bash
cd C:\Users\slama\first-cc\Warehouse-s && python -m pytest tests/ -v --timeout=30 2>&1 | head -50
```

- [ ] **Step 3: 验证模板下载端点**

启动服务后：
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/items/import/template?format=csv
```

期望：返回包含表头的 CSV 文件，Content-Type 为 text/csv。

- [ ] **Step 4: 提交最终验证结果**
```bash
git add -A && git diff --cached --stat
```
确认所有变更文件在预期范围内。
