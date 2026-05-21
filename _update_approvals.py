import re

with open('frontend/templates/pages/approvals.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 4 stat cards
old_cards = '<div class="stats-grid" style="margin-bottom:20px;">\n  <div class="stat-card"><div class="stat-value" id="stat-pending">--</div><div class="stat-label">待审核</div></div>\n  <div class="stat-card"><div class="stat-value" id="stat-overtime">--</div><div class="stat-label">已超时</div></div>\n  <div class="stat-card"><div class="stat-value" id="stat-today">--</div><div class="stat-label">今日处理</div></div>\n</div>'
new_cards = '<div class="stats-grid" style="margin-bottom:20px;">\n  <div class="stat-card"><div class="stat-value" id="stat-pending">--</div><div class="stat-label">待审核(租借)</div></div>\n  <div class="stat-card"><div class="stat-value" id="stat-transfer">--</div><div class="stat-label">待审核(调拨)</div></div>\n  <div class="stat-card"><div class="stat-value" id="stat-overtime">--</div><div class="stat-label">已超时</div></div>\n  <div class="stat-card"><div class="stat-value" id="stat-today">--</div><div class="stat-label">今日处理</div></div>\n</div>'
content = content.replace(old_cards, new_cards)
print('Stats cards updated')

# 2. Add filter
content = content.replace(
    '<div id="approvals-table-container">',
    '<div class="filter-bar" style="margin-bottom:16px;">\n  <select id="approval-type" class="form-select" onchange="loadApprovals(1)">\n    <option value="all">全部待审核</option>\n    <option value="records">物品租借</option>\n    <option value="transfers">仓库调拨</option>\n  </select>\n</div>\n<div id="approvals-table-container">'
)
print('Filter added')

# 3. Update loadStats
content = content.replace(
    "document.getElementById('stat-pending').textContent = d.total_pending;\n    document.getElementById('stat-overtime').textContent = d.total_overtime;\n    document.getElementById('stat-today').textContent = d.today_processed;",
    "document.getElementById('stat-pending').textContent = d.total_pending;\n    document.getElementById('stat-transfer').textContent = d.transfer_pending || 0;\n    document.getElementById('stat-overtime').textContent = d.total_overtime;\n    document.getElementById('stat-today').textContent = d.today_processed;"
)
print('Stats load updated')

# 4. Replace loadApprovals function
start = content.find('async function loadApprovals(page = 1) {')
end = content.find('\nasync function doApprove(id) {')

new_load = '''async function loadApprovals(page = 1) {
  approvalPage = page;
  const type = document.getElementById('approval-type').value;
  const container = document.getElementById('approvals-table-container');

  let recData = null, trData = null;
  if (type !== 'transfers') {
    const resp = await api('/api/v1/approvals/pending-grouped?page=' + page + '&page_size=15');
    if (resp.ok) recData = await resp.json();
  }
  if (type !== 'records') {
    const resp2 = await api('/api/v1/approvals/pending-transfers?page=' + page + '&page_size=15');
    if (resp2.ok) trData = await resp2.json();
  }

  const recDocs = recData ? recData.documents || [] : [];
  const trDocs = trData ? trData.groups || [] : [];
  const allDocs = recDocs.concat(trDocs);

  if (allDocs.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="icon"><i class="bi bi-clipboard-check"></i></div><p>暂无待审核记录</p></div>';
    return;
  }

  let html = '';
  for (const doc of recDocs) {
    const hasDocNo = doc.document_no !== null;
    const label = hasDocNo ? '单据号: ' + doc.document_no : '单条记录';
    const docKey = hasDocNo ? doc.document_no : doc.record_ids[0];
    const os = doc.is_overtime ? ' style="border-left:3px solid var(--danger);"' : '';
    html += '<div class="doc-group"' + os + '><div class="doc-group-header" onclick="toggleDocGroup(this)"><div class="doc-group-meta">';
    html += '<strong>' + label + '</strong>';
    html += '<span class="status-badge approved" style="font-size:11px;">物品租借</span>';
    html += '<span>借用人: ' + escapeHtml(doc.borrower_name || '') + '</span>';
    html += '<span>' + doc.item_count + ' 件物品</span>';
    html += '<span>' + (doc.borrow_date || '') + ' ~ ' + (doc.expected_return_date || '') + '</span>';
    if (doc.is_overtime) html += '<span class="status-badge overdue">超时</span>';
    html += '<span>审核截止: ' + (doc.earliest_deadline || '-') + '</span>';
    html += '</div><div style="display:flex;align-items:center;gap:8px;">';
    html += '<button class="btn btn-success btn-sm" onclick="event.stopPropagation();approveByDocument(\'' + docKey + '\')">全部通过</button>';
    html += '<button class="btn btn-danger btn-sm" onclick="event.stopPropagation();rejectByDocument(\'' + docKey + '\')">全部驳回</button>';
    html += '<span class="doc-group-toggle">▼</span></div></div>';
    html += '<div class="doc-group-body"><table class="table"><thead><tr><th>ID</th><th>物品</th><th>数量</th><th>借出日期</th><th>预计归还</th><th>操作</th></tr></thead><tbody>';
    for (const r of doc.items) {
      html += '<tr><td>' + r.id + '</td><td>' + escapeHtml(r.item_name || '') + '</td><td>' + r.quantity + '</td><td>' + (r.borrow_date || '') + '</td><td>' + (r.expected_return_date || '') + '</td>';
      html += '<td><div class="btn-group"><button class="btn btn-success btn-sm" onclick="doApproveWithConfirm(' + r.id + ')">通过</button><button class="btn btn-danger btn-sm" onclick="showRejectDialogForId(' + r.id + ')">驳回</button></div></td></tr>';
    }
    html += '</tbody></table></div></div>';
  }

  for (const g of trDocs) {
    html += '<div class="doc-group"><div class="doc-group-header" onclick="toggleDocGroup(this)"><div class="doc-group-meta">';
    html += '<strong>' + escapeHtml(g.document_no || '') + '</strong>';
    html += '<span class="status-badge pending" style="font-size:11px;">仓库调拨</span>';
    html += '<span><i class="bi bi-building"></i> ' + escapeHtml(g.from_warehouse_name || '') + ' <i class="bi bi-arrow-right"></i> ' + escapeHtml(g.to_warehouse_name || '') + '</span>';
    html += '<span>' + (g.count || g.items.length) + ' 件物品</span>';
    html += '<span>' + escapeHtml(g.created_by_name || '') + '</span>';
    html += '<span>' + (g.created_at || '') + '</span>';
    html += '</div><div style="display:flex;align-items:center;gap:8px;">';
    html += '<button class="btn btn-success btn-sm" onclick="event.stopPropagation();approveTransferDocument(\'' + escapeHtml(g.document_no || '') + '\')">全部通过</button>';
    html += '<button class="btn btn-danger btn-sm" onclick="event.stopPropagation();showRejectTransferDialog(\'' + escapeHtml(g.document_no || '') + '\')">全部驳回</button>';
    html += '<span class="doc-group-toggle">▼</span></div></div>';
    html += '<div class="doc-group-body"><table class="table"><thead><tr><th>ID</th><th>物品</th><th>源→目标</th><th>数量</th><th>操作</th></tr></thead><tbody>';
    for (const t of g.items) {
      html += '<tr><td>' + t.id + '</td><td>' + escapeHtml(t.item_name || '') + '</td>';
      html += '<td>' + escapeHtml(t.from_warehouse_name || '') + ' <i class="bi bi-arrow-right"></i> ' + escapeHtml(t.to_warehouse_name || '') + '</td>';
      html += '<td>' + t.quantity + '</td>';
      html += '<td><div class="btn-group"><button class="btn btn-success btn-sm" onclick="doApproveTransfer(' + t.id + ')">通过</button><button class="btn btn-danger btn-sm" onclick="showRejectTransferForId(' + t.id + ')">驳回</button></div></td></tr>';
    }
    html += '</tbody></table></div></div>';
  }

  container.innerHTML = html;
  const totalItems = recDocs.length + trDocs.length;
  const pages = Math.ceil(totalItems / 15);
  if (pages > 1) {
    let pg = '<div class="pagination">';
    pg += '<button onclick="loadApprovals(' + (page-1) + ')" ' + (page===1?'disabled':'') + '>上一页</button>';
    for (let i = 1; i <= pages; i++) pg += '<button class="' + (i===page?'active':'') + '" onclick="loadApprovals(' + i + ')">' + i + '</button>';
    pg += '<button onclick="loadApprovals(' + (page+1) + ')" ' + (page===pages?'disabled':'') + '>下一页</button></div>';
    container.innerHTML += pg;
  }
}

// ── 调拨审核操作 ──
async function doApproveTransfer(id) {
  const resp = await api('/api/v1/transfers/' + id + '/approve', { method: 'PUT' });
  if (resp.ok) { showToast('已通过'); loadApprovals(approvalPage); loadStats(); }
  else { const d = await resp.json(); showToast(d.detail, 'error'); }
}

async function approveTransferDocument(docNo) {
  showConfirmDialog('确认全部通过', '确定通过调拨单 ' + docNo + ' 的所有物品吗？', async () => {
    const resp = await api('/api/v1/transfers/by-document/' + encodeURIComponent(docNo) + '/approve', { method: 'PUT' });
    if (resp.ok) { const d = await resp.json(); showToast(d.message || '已全部通过'); loadApprovals(approvalPage); loadStats(); }
    else { const d = await resp.json(); showToast(d.detail, 'error'); }
  });
}

function showRejectTransferForId(id) {
  showRejectDialog('驳回调拨', '确定驳回该调拨申请吗？', async (reason) => {
    const resp = await api('/api/v1/transfers/' + id + '/reject', { method: 'PUT', body: JSON.stringify({ reason }) });
    if (resp.ok) { showToast('已驳回'); loadApprovals(approvalPage); loadStats(); }
    else { const d = await resp.json(); showToast(d.detail, 'error'); }
  });
}

function showRejectTransferDialog(docNo) {
  showRejectDialog('全部驳回', '确定驳回调拨单 ' + docNo + ' 的所有物品吗？', async (reason) => {
    const resp = await api('/api/v1/transfers/by-document/' + encodeURIComponent(docNo) + '/reject', { method: 'PUT', body: JSON.stringify({ reason }) });
    if (resp.ok) { showToast('已全部驳回'); loadApprovals(approvalPage); loadStats(); }
    else { const d = await resp.json(); showToast(d.detail, 'error'); }
  });
}

'''

content = content[:start] + new_load + content[end:]
print('loadApprovals replaced')

with open('frontend/templates/pages/approvals.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done - approvals page updated')
