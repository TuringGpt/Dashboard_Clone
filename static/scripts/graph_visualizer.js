// Graph Visualizer JavaScript

let currentDataset = null;
let schema = null;          // {tables, colors, hint_fields, flows, options}
let graphData = null;       // last rendered graph payload
let render = null;          // ForceGraph renderer instance
let lockedMode = false;     // lock toggle: only show focal + 1-hop neighbors
let deepLockedMode = false; // deep lock: show focal + all transitive descendants

const API = '/clone/graph_visualizer';

// fetch with retry/backoff. The Flask dev server uses the Werkzeug reloader,
// which restarts the worker when a watched file changes; during the restart the
// server is briefly unreachable and fetch() rejects with a TypeError ("Failed
// to fetch"). Retrying a few times lets the request succeed once the worker is
// back instead of hard-failing the whole action.
// fetch with retry on network errors only (server unreachable / restarting).
// No artificial timeout — the server processes in <1s; if it's slow it's
// because it's restarting, and retrying handles that.
async function apiFetch(url, opts = {}, { retries = 2, baseDelay = 500 } = {}) {
    let lastErr;
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            const res = await fetch(url, opts);
            return res;
        } catch (err) {
            lastErr = err;
            // Only retry on network errors (TypeError = fetch failed entirely).
            // HTTP errors (4xx/5xx) are NOT retried — they're real responses.
            if (!(err instanceof TypeError) || attempt === retries) throw err;
            const delay = Math.min(baseDelay * Math.pow(2, attempt), 4000);
            await new Promise(r => setTimeout(r, delay));
        }
    }
    throw lastErr;
}

function netErrMessage(err) {
    if (err instanceof TypeError && /Failed to fetch/i.test(err.message)) {
        return 'Could not reach the server. It may be restarting or not running. ' +
               'The request was retried automatically; please retry manually if it keeps failing.';
    }
    return err.message || String(err);
}

document.addEventListener('DOMContentLoaded', () => {
    loadDatasets();
    setupUpload();
    setupFilters();
    setupCanvasControls();
});

// ---------------------------------------------------------------------------
// Datasets list
// ---------------------------------------------------------------------------
async function loadDatasets() {
    try {
        const res = await apiFetch(`${API}/datasets`);
        const data = await res.json();
        renderDatasetCards(data.datasets || []);
        populateDatasetDropdown(data.datasets || []);
    } catch (e) {
        renderDatasetCards([]);
    }
}

function renderDatasetCards(datasets) {
    const container = document.getElementById('dataset-cards');
    if (!datasets.length) {
        container.innerHTML = '<div class="loading">No datasets uploaded yet. Use the Upload card to add one.</div>';
        return;
    }
    container.innerHTML = datasets.map(d => `
        <div class="db-card" data-id="${d.id}">
            <div class="db-name">${escapeHtml(d.name)}</div>
            <div class="db-stats">
                Tables: ${d.summary.tables || 0} &middot; Rows: ${d.summary.rows || 0}<br>
                Graphs: ${d.summary.graphs || 0} &middot; Flows: ${d.summary.flows || 0}<br>
                Largest graph: ${d.summary.largest_graph || 0} nodes
            </div>
            <div class="db-actions">
                <button class="mini-btn" data-act="visualize">Visualize</button>
                <button class="mini-btn danger" data-act="delete">Delete</button>
            </div>
        </div>`).join('');

    container.querySelectorAll('.db-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.classList.contains('mini-btn')) return;
            openVisualizer(card.dataset.id);
        });
    });
    container.querySelectorAll('.mini-btn[data-act="visualize"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            openVisualizer(btn.closest('.db-card').dataset.id);
        });
    });
    container.querySelectorAll('.mini-btn[data-act="delete"]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const card = btn.closest('.db-card');
            await deleteDataset(card.dataset.id, card);
        });
    });
}

async function deleteDataset(datasetId, cardEl) {
    if (!confirm(`Delete dataset "${datasetId}"? This cannot be undone.`)) return;
    try {
        const res = await apiFetch(`${API}/delete/${datasetId}`, { method: 'POST' });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') throw new Error(data.message || 'Delete failed');
        if (cardEl) cardEl.remove();
        if (currentDataset === datasetId) {
            currentDataset = null;
            schema = null;
            clearGraph();
            document.getElementById('dataset-select').value = '';
            document.getElementById('flow-select').innerHTML = '<option value="">All flows</option>';
            document.getElementById('table-select').innerHTML = '<option value="">-- Select a table --</option>';
            resetIdCombo();
            document.getElementById('visualize-btn').disabled = true;
        }
        await loadDatasets();
    } catch (e) {
        alert('Delete failed: ' + netErrMessage(e));
    }
}

function populateDatasetDropdown(datasets) {
    const sel = document.getElementById('dataset-select');
    sel.innerHTML = '<option value="">-- Select a dataset --</option>' +
        datasets.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');
}

// ---------------------------------------------------------------------------
// Upload handling
// ---------------------------------------------------------------------------
function setupUpload() {
    document.getElementById('upload-card').addEventListener('click', () => {
        showSection('upload-section');
    });
    document.getElementById('visualize-card').addEventListener('click', () => {
        showSection('visualizer-section');
    });

    setupDropZone('zip-drop-zone', 'sql-zip', 'zip-file-name', '.zip');
    setupDropZone('yaml-drop-zone', 'yaml-file', 'yaml-file-name', '.yaml,.yml');

    document.getElementById('upload-btn').addEventListener('click', uploadDataset);
    setupYamlPromptModal();
}

let _yamlPromptText = null;
function setupYamlPromptModal() {
    const modal = document.getElementById('yaml-prompt-modal');
    const showBtn = document.getElementById('show-yaml-prompt');
    const copyBtn = document.getElementById('copy-yaml-prompt');
    const body = document.getElementById('yaml-prompt-body');

    showBtn.addEventListener('click', async () => {
        modal.style.display = 'flex';
        if (_yamlPromptText === null) {
            body.textContent = 'Loading...';
            try {
                const res = await apiFetch(`${API}/yaml_prompt`);
                const data = await res.json();
                if (data.status !== 'success') throw new Error(data.message);
                _yamlPromptText = data.prompt;
                body.textContent = _yamlPromptText;
            } catch (e) {
                _yamlPromptText = '';
                body.textContent = 'Failed to load prompt: ' + netErrMessage(e);
            }
        } else {
            body.textContent = _yamlPromptText || '(empty)';
        }
    });

    // Click outside the card closes the modal.
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.style.display = 'none'; });

    copyBtn.addEventListener('click', async () => {
        if (!_yamlPromptText) return;
        try {
            await navigator.clipboard.writeText(_yamlPromptText);
            copyBtn.textContent = 'Copied!';
            setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1500);
        } catch {
            // Fallback for non-secure contexts.
            const ta = document.createElement('textarea');
            ta.value = _yamlPromptText;
            document.body.appendChild(ta);
            ta.select();
            try { document.execCommand('copy'); copyBtn.textContent = 'Copied!'; setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1500); }
            catch { copyBtn.textContent = 'Press Ctrl+C'; setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1500); }
            document.body.removeChild(ta);
        }
    });
}

function setupDropZone(zoneId, inputId, labelId, accept) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    const label = document.getElementById(labelId);

    input.addEventListener('change', (e) => {
        if (e.target.files.length) label.textContent = e.target.files[0].name;
    });

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
    });
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            const f = e.dataTransfer.files[0];
            input.files = e.dataTransfer.files;
            label.textContent = f.name;
        }
    });
}

async function uploadDataset() {
    const zipFile = document.getElementById('sql-zip').files[0];
    const yamlFile = document.getElementById('yaml-file').files[0];
    const name = document.getElementById('dataset-name').value.trim();
    const status = document.getElementById('upload-status');

    if (!zipFile) {
        showStatus(status, 'A zipped .sql file is required.', 'error');
        return;
    }

    const fd = new FormData();
    fd.append('sql_zip', zipFile);
    if (yamlFile) fd.append('yaml', yamlFile);
    if (name) fd.append('name', name);

    showStatus(status, 'Processing...', 'info');
    document.getElementById('upload-btn').disabled = true;

    try {
        const res = await apiFetch(`${API}/upload`, { method: 'POST', body: fd },
            { retries: 1 });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            throw new Error(data.message || 'Upload failed');
        }
        showStatus(status,
            `Dataset "${data.name}" created. Tables: ${data.summary.tables}, ` +
            `Rows: ${data.summary.rows}, Graphs: ${data.summary.graphs}, ` +
            `Flows: ${data.summary.flows}.`, 'success');
        await loadDatasets();
        openVisualizer(data.dataset_id);
    } catch (e) {
        if (e instanceof TypeError && /Failed to fetch/.test(e.message)) {
            showStatus(status,
                'Could not reach the server (connection reset). The dev reloader ' +
                'may be restarting the worker, or the server is not running. ' +
                'Restart the server and retry, or run with FLASK_ENV=production.', 'error');
        } else {
            showStatus(status, netErrMessage(e), 'error');
        }
    } finally {
        document.getElementById('upload-btn').disabled = false;
    }
}

// ---------------------------------------------------------------------------
// Searchable id combobox
// ---------------------------------------------------------------------------
let idItems = [];         // current list of {pk, label, table, graph_id, graph_size, flow_id}
let idComboReqId = 0;     // monotonic request id to cancel stale loadIds
let idHighlightIdx = -1;
let selectedIdItem = null; // the id item chosen from the dropdown (carries its real .table for "All tables")

function resetIdCombo() {
    idItems = [];
    selectedIdItem = null;
    const input = document.getElementById('id-input');
    if (input) input.value = '';
    const hidden = document.getElementById('id-value');
    if (hidden) hidden.value = '';
    const dd = document.getElementById('id-dropdown');
    if (dd) { dd.classList.remove('open'); dd.innerHTML = ''; }
    const idCnt = document.getElementById('id-count');
    if (idCnt) { idCnt.textContent = ''; idCnt.classList.remove('filter-active'); }
}

function setupIdCombo() {
    const input = document.getElementById('id-input');
    const dd = document.getElementById('id-dropdown');

    input.addEventListener('input', () => {
        document.getElementById('id-value').value = '';
        selectedIdItem = null;
        filterIdCombo(input.value);
        dd.classList.add('open');
    });

    input.addEventListener('focus', () => {
        if (idItems.length) { filterIdCombo(input.value); dd.classList.add('open'); }
    });

    input.addEventListener('keydown', (e) => {
        const items = dd.querySelectorAll('.combo-item');
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            idHighlightIdx = Math.min(idHighlightIdx + 1, items.length - 1);
            updateHighlight(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            idHighlightIdx = Math.max(idHighlightIdx - 1, 0);
            updateHighlight(items);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (idHighlightIdx >= 0 && items[idHighlightIdx]) {
                items[idHighlightIdx].click();
            } else if (items.length > 0) {
                items[0].click();
            }
        } else if (e.key === 'Escape') {
            dd.classList.remove('open');
        }
    });

    document.addEventListener('click', (e) => {
        if (!document.getElementById('id-combo').contains(e.target)) {
            dd.classList.remove('open');
        }
    });
}

function updateHighlight(items) {
    items.forEach((el, i) => el.classList.toggle('highlighted', i === idHighlightIdx));
    if (idHighlightIdx >= 0 && items[idHighlightIdx]) {
        items[idHighlightIdx].scrollIntoView({ block: 'nearest' });
    }
}

function filterIdCombo(query) {
    const dd = document.getElementById('id-dropdown');
    idHighlightIdx = -1;
    const q = query.toLowerCase().trim();
    const filtered = q ? idItems.filter(i =>
        (i.label && i.label.toLowerCase().includes(q)) ||
        (i.pk && i.pk.toLowerCase().includes(q)) ||
        (i.table && i.table.toLowerCase().includes(q))
    ) : idItems;

    if (!filtered.length) {
        dd.innerHTML = `<div class="combo-empty">${q ? 'No matches' : 'No ids available'}</div>`;
        return;
    }
    // Cap the number of rendered rows so huge lists (e.g. "All tables") stay responsive.
    const RENDER_CAP = 400;
    const shown = filtered.slice(0, RENDER_CAP);
    const tableTag = (item) => item.table
        ? `<span class="combo-table"> — ${escapeHtml(item.table)}</span>` : '';
    dd.innerHTML = shown.map((item, idx) => `
        <div class="combo-item" data-pk="${escapeAttr(item.pk)}" data-table="${escapeAttr(item.table || '')}" data-idx="${idx}">
            <span class="combo-label">${escapeHtml(item.label || item.pk)}</span>
            <span class="combo-meta">${tableTag(item)} — ${escapeHtml(truncate(item.pk, 40))} (graph ${item.graph_id}, ${item.graph_size})</span>
        </div>`).join('');
    if (filtered.length > shown.length) {
        dd.innerHTML += `<div class="combo-empty">…${filtered.length - shown.length} more — keep typing to filter</div>`;
    }

    dd.querySelectorAll('.combo-item').forEach(el => {
        el.addEventListener('click', () => {
            const pk = el.dataset.pk;
            const tbl = el.dataset.table;
            const item = idItems.find(i => i.pk === pk && (!tbl || i.table === tbl));
            if (!item) return;
            selectedIdItem = item;
            document.getElementById('id-input').value = item.label || item.pk;
            document.getElementById('id-value').value = item.pk;
            dd.classList.remove('open');
            document.getElementById('visualize-btn').disabled = false;
        });
    });
}

// ---------------------------------------------------------------------------
// Filters + visualization
// ---------------------------------------------------------------------------
function setupFilters() {
    document.getElementById('dataset-select').addEventListener('change', async (e) => {
        const id = e.target.value;
        if (!id) return;
        await loadSchema(id);
    });

    document.getElementById('table-select').addEventListener('change', async (e) => {
        const table = e.target.value;
        resetIdCombo();
        if (!table) {
            document.getElementById('visualize-btn').disabled = true;
            return;
        }
        await loadIds(table);
    });

    document.getElementById('flow-select').addEventListener('change', async () => {
        filterTableDropdown();
        resetIdCombo();
        const table = document.getElementById('table-select').value;
        if (table) await loadIds(table);
        // Enable Connect when a flow is selected even without a specific id.
        const flowId = document.getElementById('flow-select').value;
        if (flowId) document.getElementById('visualize-btn').disabled = false;
    });

    document.getElementById('visualize-btn').addEventListener('click', visualize);
    setupIdCombo();
    setupLockToggle();
}

function setupLockToggle() {
    const btn = document.getElementById('lock-toggle');
    const deepBtn = document.getElementById('lock-deep');
    if (!btn) return;

    const applyLock = (isDeep) => {
        if (isDeep) {
            deepLockedMode = !deepLockedMode;
            if (deepLockedMode) {
                // Turn off regular lock if on.
                if (lockedMode) { lockedMode = false; btn.classList.remove('active'); const ic = btn.querySelector('.lock-icon'); if (ic) ic.textContent = '🔓'; btn.title = 'Lock OFF: show the full connected component'; }
            }
        } else {
            lockedMode = !lockedMode;
            if (lockedMode) {
                // Turn off deep lock if on.
                if (deepLockedMode) { deepLockedMode = false; deepBtn.classList.remove('active'); const dic = deepBtn.querySelector('.lock-icon'); if (dic) dic.textContent = '🌳'; deepBtn.title = 'Deep lock OFF: show full component'; }
            }
        }
    };

    btn.addEventListener('click', () => {
        applyLock(false);
        btn.classList.toggle('active', lockedMode);
        const icon = btn.querySelector('.lock-icon');
        if (icon) icon.textContent = lockedMode ? '🔒' : '🔓';
        btn.title = lockedMode
            ? 'Lock ON: only the selected item + its direct neighbors'
            : 'Lock OFF: show the full connected component';
        if (render) render.toggleLock();
    });

    if (deepBtn) {
        deepBtn.addEventListener('click', () => {
            applyLock(true);
            deepBtn.classList.toggle('active', deepLockedMode);
            const icon = deepBtn.querySelector('.lock-icon');
            if (icon) icon.textContent = deepLockedMode ? '🌲' : '🌳';
            deepBtn.title = deepLockedMode
                ? 'Deep lock ON: show the selected item + all descendants to the leaves'
                : 'Deep lock OFF: show full component';
            if (render) render.toggleDeepLock();
        });
    }
}

function filterTableDropdown() {
    if (!schema) return;
    const flowId = document.getElementById('flow-select').value;
    const tableSel = document.getElementById('table-select');
    const currentTable = tableSel.value;
    let tables = schema.tables;
    if (flowId) {
        const flowObj = schema.flows.find(t => String(t.flow_id) === flowId);
        const typeTables = flowObj ? new Set(flowObj.tables) : new Set();
        tables = tables.filter(t => typeTables.has(t.name));
    }
    tableSel.innerHTML = '<option value="">-- Select a table --</option>' +
        '<option value="__all__">All tables</option>' +
        tables.map(t => `<option value="${t.name}">${t.name} (${t.row_count})</option>`).join('');
    // Show filtered count: "N of total tables"
    const total = (schema.tables || []).length;
    const cnt = document.getElementById('table-count');
    cnt.textContent = flowId ? `(${tables.length} of ${total} tables)` : `(${total} tables)`;
    cnt.classList.toggle('filter-active', !!flowId && tables.length < total);
    // if current table is no longer in the filtered list, reset it
    if (currentTable && currentTable !== '__all__' && !tables.find(t => t.name === currentTable)) {
        tableSel.value = '';
    } else {
        tableSel.value = currentTable;
    }
}

function openVisualizer(datasetId) {
    showSection('visualizer-section');
    document.getElementById('visualizer-section').scrollIntoView({ behavior: 'smooth' });
    if (datasetId) {
        document.getElementById('dataset-select').value = datasetId;
        loadSchema(datasetId);
    }
}

async function loadSchema(datasetId) {
    const status = document.getElementById('load-status');
    currentDataset = datasetId;
    try {
        const res = await apiFetch(`${API}/schema/${datasetId}`);
        const data = await res.json();
        if (data.status !== 'success') throw new Error(data.message);

        schema = data;

        // Flow dropdown
        const flowSel = document.getElementById('flow-select');
        const flows = data.flows || [];
        flowSel.innerHTML = '<option value="">All flows</option>' +
            flows.map(t => `
                <option value="${t.flow_id}">Flow ${t.flow_id} — ${t.tables.join(', ')} (${t.count})</option>
            `).join('');
        document.getElementById('flow-count').textContent = `(${flows.length} flows)`;

        // Table dropdown (with "All tables" option)
        const tableSel = document.getElementById('table-select');
        const tables = data.tables || [];
        tableSel.innerHTML = '<option value="">-- Select a table --</option>' +
            '<option value="__all__">All tables</option>' +
            tables.map(t => `
                <option value="${t.name}">${t.name} (${t.row_count})</option>
            `).join('');
        document.getElementById('table-count').textContent = `(${tables.length} tables)`;
        document.getElementById('id-count').textContent = '';

        // Legend (full color legend for all tables)
        renderLegend(data.tables, null);

        // Reset id combo
        resetIdCombo();
        document.getElementById('visualize-btn').disabled = true;
        clearGraph();
        showStatus(status, `Loaded schema for "${data.name}".`, 'success');
    } catch (e) {
        showStatus(status, netErrMessage(e), 'error');
    }
}

async function loadIds(table) {
    const flowId = document.getElementById('flow-select').value;
    const input = document.getElementById('id-input');
    const dd = document.getElementById('id-dropdown');
    const myReqId = ++idComboReqId;

    input.value = '';
    document.getElementById('id-value').value = '';
    input.placeholder = 'Loading ids...';
    dd.innerHTML = '<div class="combo-empty">Loading...</div>';
    dd.classList.add('open');
    idItems = [];
    document.getElementById('visualize-btn').disabled = true;

    // For a single table, fetch all ids (capped by the backend's per-table limit).
    // For "All tables", sample per table so the dropdown stays browsable.
    const isAll = (table === '__all__');
    const url = `${API}/ids/${currentDataset}?table=${encodeURIComponent(table)}` +
        (isAll ? `&sample=10` : `&limit=5000`) + (flowId ? `&flow=${flowId}` : '');
    try {
        const res = await apiFetch(url);
        // discard stale responses (user switched table/flow while we were loading)
        if (myReqId !== idComboReqId) return;
        const data = await res.json();
        if (data.status !== 'success') throw new Error(data.message);

        idItems = data.ids || [];
        input.placeholder = `Type to search ${data.count} id${data.count !== 1 ? 's' : ''}...`;
        const idCnt = document.getElementById('id-count');
        idCnt.textContent = `(${data.count} of ${data.total} ids)`;
        idCnt.classList.toggle('filter-active', data.count < data.total);
        filterIdCombo('');
        document.getElementById('visualize-btn').disabled = (idItems.length === 0);
    } catch (e) {
        if (myReqId !== idComboReqId) return;
        input.placeholder = 'Error loading ids';
        dd.innerHTML = `<div class="combo-empty">${escapeHtml(netErrMessage(e))}</div>`;
        dd.classList.add('open');
    }
}

async function visualize() {
    let table = document.getElementById('table-select').value;
    const id = document.getElementById('id-value').value;
    const flowId = document.getElementById('flow-select').value;
    const status = document.getElementById('load-status');
    if (!currentDataset) {
        showStatus(status, 'Pick a dataset, table, and id from the dropdowns first, then click Connect.', 'error');
        return;
    }
    // "All tables" isn't a real table — resolve to the selected id's actual table.
    if (table === '__all__') {
        table = selectedIdItem ? selectedIdItem.table : '';
    }

    // No specific id: if a flow is selected, show a representative graph from it.
    if (!id) {
        if (!flowId) {
            showStatus(status, 'Pick an id from the dropdown, or select a flow first, then click Connect.', 'error');
            return;
        }
        showStatus(status, `Loading a sample graph from flow ${flowId}...`, 'info');
        document.getElementById('visualize-btn').disabled = true;
        try {
            const url = `${API}/flow_sample/${currentDataset}?flow=${flowId}` + (lockedMode ? '&lock=1' : '');
            const res = await apiFetch(url);
            const data = await res.json();
            if (data.status !== 'success') throw new Error(data.message);
            graphData = data;
            renderGraph(data);
            reapplyLock();
            showStatus(status,
                `Flow ${data.flow_id} sample — graph ${data.graph_id}: ${data.graph_size} connected nodes ` +
                `(showing ${data.rendered_count}${data.truncated ? ', capped' : ''}${lockLabel()}).`,
                'success');
        } catch (e) {
            showStatus(status, netErrMessage(e), 'error');
        } finally {
            document.getElementById('visualize-btn').disabled = false;
        }
        return;
    }

    if (!table) {
        showStatus(status, 'Pick a table and an id from the dropdowns first, then click Connect.', 'error');
        return;
    }
    showStatus(status, 'Loading graph...', 'info');
    document.getElementById('visualize-btn').disabled = true;
    try {
        const res = await apiFetch(`${API}/graph/${currentDataset}?table=${encodeURIComponent(table)}&id=${encodeURIComponent(id)}`);
        const data = await res.json();
        if (data.status !== 'success') throw new Error(data.message);

        graphData = data;
        renderGraph(data);
        // If lock was active, re-apply it client-side on the new graph.
        reapplyLock();
        showStatus(status,
            `Graph ${data.graph_id}: ${data.graph_size} connected nodes ` +
            `(showing ${data.rendered_count}${data.truncated ? ', capped' : ''}${lockLabel()}, flow ${data.flow_id}).`,
            'success');
    } catch (e) {
        showStatus(status, netErrMessage(e), 'error');
    } finally {
        document.getElementById('visualize-btn').disabled = false;
    }
}

// ---------------------------------------------------------------------------
// Legend
// ---------------------------------------------------------------------------
function renderLegend(tables, counts) {
    const container = document.getElementById('legend-items');
    // tables may be the schema table list OR a list of {name,color}
    const items = (tables || []).map(t => {
        const name = t.name || t;
        const color = t.color || (schema && schema.colors && schema.colors[name]) || '#888';
        const count = counts ? (counts[name] || 0) : (t.row_count || '');
        return { name, color, count };
    });
    container.innerHTML = items.map(it => `
        <div class="legend-item" data-table="${escapeAttr(it.name)}">
            <span class="legend-swatch" style="background:${it.color}"></span>
            <span>${escapeHtml(it.name)}</span>
            <span class="legend-count">${it.count !== '' ? it.count : ''}</span>
        </div>`).join('');

    container.querySelectorAll('.legend-item').forEach(el => {
        el.addEventListener('click', () => {
            if (render) render.toggleTable(el.dataset.table, el);
        });
    });
}

// ---------------------------------------------------------------------------
// Force-directed graph renderer (canvas)
// ---------------------------------------------------------------------------
class ForceGraph {
    constructor(canvasId, metaId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.meta = document.getElementById(metaId);
        this.nodes = [];
        this.edges = [];
        this.nodeMap = {};
        this.colors = {};
        this.hiddenTables = new Set();

        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.isDragging = false;
        this.dragNode = null;
        this.lastMouse = { x: 0, y: 0 };
        this.hoverNode = null;

        this.running = false;
        this.alpha = 1;

        // Lock overlay state (client-side, animated)
        this.locked = false;
        this.lockCenter = null;        // node id at the center of the lock
        this.lockNeighbors = new Set(); // node ids that are 1-hop from lockCenter (incl. center)
        this.lockAlpha = 0;             // 0 = fully unlocked, 1 = fully locked (animated)

        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.setupInteraction();
        this.tick = this.tick.bind(this);
    }

    resize() {
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        this.width = rect.width;
        this.height = rect.height;
        if (this.nodes.length) this.draw();
    }

    setData(data) {
        this.colors = data.colors || {};
        this.hiddenTables.clear();
        // Build nodes
        this.nodes = data.nodes.map(n => ({
            id: n.id,
            table: n.table,
            pk: n.pk,
            label: n.label,
            fields: n.fields,
            full_fields: n.full_fields,
            isFocal: n.is_focal,
            x: this.width / 2 + (Math.random() - 0.5) * 200,
            y: this.height / 2 + (Math.random() - 0.5) * 200,
            vx: 0, vy: 0,
            r: n.is_focal ? 9 : 6,
        }));
        this.nodeMap = {};
        this.nodes.forEach(n => { this.nodeMap[n.id] = n; });
        // Build edges
        this.edges = (data.edges || []).map(e => ({
            source: this.nodeMap[e.source],
            target: this.nodeMap[e.target],
            field: e.field,
        })).filter(e => e.source && e.target);

        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.alpha = 1;
        // Reset lock overlay state for the new graph.
        this.locked = false;
        this.lockCenter = null;
        this.lockNeighbors = new Set();
        this.lockAlpha = 0;
        this.selectedNode = null;
        this.start();
    }

    start() {
        if (this.running) return;
        this.running = true;
        requestAnimationFrame(this.tick);
    }

    stop() { this.running = false; }

    tick() {
        if (!this.running) return;
        const nodes = this.nodes;
        const edges = this.edges;
        const n = nodes.length;
        if (!n) { this.stop(); return; }

        // Repulsion (O(n^2); fine for <= ~600 nodes)
        for (let i = 0; i < n; i++) {
            const a = nodes[i];
            for (let j = i + 1; j < n; j++) {
                const b = nodes[j];
                let dx = a.x - b.x;
                let dy = a.y - b.y;
                let d2 = dx * dx + dy * dy;
                if (d2 < 0.01) { d2 = 0.01; dx = 0.1; dy = 0.1; }
                const dist = Math.sqrt(d2);
                const force = (1400 * this.alpha) / d2;
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;
                a.vx += fx; a.vy += fy;
                b.vx -= fx; b.vy -= fy;
            }
        }
        // Spring (attraction along edges)
        const k = 0.04;
        for (const e of edges) {
            const dx = e.target.x - e.source.x;
            const dy = e.target.y - e.source.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
            const target = 70;
            const force = (dist - target) * k * this.alpha;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            e.source.vx += fx; e.source.vy += fy;
            e.target.vx -= fx; e.target.vy -= fy;
        }
        // Lock cluster attraction: when locked, pull each locked neighbor
        // toward the lock center so the focused cluster compacts together.
        const la = this.lockAlpha;
        if (la > 0 && this.lockCenter) {
            const center = this.nodeMap[this.lockCenter];
            if (center) {
                const pull = 0.05 * la * this.alpha;
                for (const n of nodes) {
                    if (!this.lockNeighbors.has(n.id) || n.id === this.lockCenter) continue;
                    n.vx += (center.x - n.x) * pull;
                    n.vy += (center.y - n.y) * pull;
                }
            }
        }
        // Centering + integrate
        const cx = this.width / 2;
        const cy = this.height / 2;
        let totalVel = 0;
        for (const a of nodes) {
            // Pin the drag node AND the lock center so the selected node stays
            // put while only its neighbors approach it.
            if (a === this.dragNode || (this.locked && a.id === this.lockCenter)) {
                a.vx = 0; a.vy = 0; continue;
            }
            a.vx += (cx - a.x) * 0.005 * this.alpha;
            a.vy += (cy - a.y) * 0.005 * this.alpha;
            a.vx *= 0.82; a.vy *= 0.82;
            a.x += a.vx; a.y += a.vy;
            totalVel += Math.abs(a.vx) + Math.abs(a.vy);
        }
        this.alpha *= 0.95;
        this.draw();
        // Stop when the graph has settled.
        if (this.alpha < 0.02 || (totalVel / n) < 0.05) {
            this.alpha = 0;
            this.running = false;
            this.draw();
            return;
        }
        requestAnimationFrame(this.tick);
    }

    draw() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.width, this.height);
        ctx.save();
        ctx.translate(this.offsetX, this.offsetY);
        ctx.scale(this.scale, this.scale);

        const la = this.lockAlpha; // 0 = unlocked, 1 = fully locked

        // Edges
        ctx.lineWidth = 1 / this.scale;
        for (const e of this.edges) {
            if (this.hiddenTables.has(e.source.table) || this.hiddenTables.has(e.target.table)) continue;
            // Dim edges that aren't between locked neighbors.
            let alpha = 0.18;
            if (la > 0) {
                const inLock = this.lockNeighbors.has(e.source.id) && this.lockNeighbors.has(e.target.id);
                alpha = inLock ? 0.18 + la * 0.3 : 0.18 * (1 - la * 0.9);
            }
            ctx.strokeStyle = `rgba(255,255,255,${alpha})`;
            ctx.beginPath();
            ctx.moveTo(e.source.x, e.source.y);
            ctx.lineTo(e.target.x, e.target.y);
            ctx.stroke();
        }

        // Nodes
        for (const n of this.nodes) {
            if (this.hiddenTables.has(n.table)) continue;
            const color = this.colors[n.table] || '#888';
            const isHover = (n === this.hoverNode);
            const isSelected = (this.selectedNode && n.id === this.selectedNode);
            const isLockCenter = (la > 0 && n.id === this.lockCenter);
            const inLock = (la > 0 && this.lockNeighbors.has(n.id));
            // Dim non-neighbor nodes when locked.
            const dim = inLock ? 1 : (1 - la * 0.82);
            const r = n.r * (n.isFocal ? 1.4 : 1) * (isHover ? 1.4 : 1) * (isSelected ? 1.3 : 1) * (isLockCenter ? 1.2 : 1);

            ctx.globalAlpha = dim;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            if (n.isFocal) {
                ctx.lineWidth = 3 / this.scale;
                ctx.strokeStyle = '#ffffff';
                ctx.stroke();
            } else if (isLockCenter) {
                ctx.lineWidth = 3 / this.scale;
                ctx.strokeStyle = '#fbbf24';
                ctx.stroke();
            } else if (isSelected) {
                ctx.lineWidth = 3 / this.scale;
                ctx.strokeStyle = '#fbbf24';
                ctx.stroke();
            } else if (isHover) {
                ctx.lineWidth = 2 / this.scale;
                ctx.strokeStyle = '#ffffff';
                ctx.stroke();
            } else {
                ctx.lineWidth = 1 / this.scale;
                ctx.strokeStyle = 'rgba(0,0,0,0.4)';
                ctx.stroke();
            }

            // Labels: show for focal/selected/locked neighbors/hovered
            const showLabel = n.isFocal || isSelected || isLockCenter || (inLock && la > 0.5) || this.scale > 1.4 || isHover;
            if (showLabel && dim > 0.15) {
                ctx.globalAlpha = dim;
                ctx.fillStyle = isSelected || isLockCenter ? '#fbbf24' : 'rgba(255,255,255,0.9)';
                ctx.font = `${11 / this.scale}px sans-serif`;
                ctx.textAlign = 'center';
                ctx.fillText(truncate(n.label, 24), n.x, n.y - r - 3 / this.scale);
            }
            ctx.globalAlpha = 1;
        }
        ctx.restore();
    }

    // Convert screen coords to world coords
    toWorld(sx, sy) {
        return {
            x: (sx - this.offsetX) / this.scale,
            y: (sy - this.offsetY) / this.scale,
        };
    }

    nodeAt(sx, sy) {
        const p = this.toWorld(sx, sy);
        // iterate from end (drawn last = on top)
        for (let i = this.nodes.length - 1; i >= 0; i--) {
            const n = this.nodes[i];
            if (this.hiddenTables.has(n.table)) continue;
            // When locked, skip dimmed-out nodes (can't click what you can't see well).
            if (this.lockAlpha > 0.5 && this.locked && !this.lockNeighbors.has(n.id)) continue;
            const dx = p.x - n.x;
            const dy = p.y - n.y;
            const r = n.r * (n.isFocal ? 1.4 : 1) + 4 / this.scale;
            if (dx * dx + dy * dy <= r * r) return n;
        }
        return null;
    }

    setupInteraction() {
        const c = this.canvas;
        c.addEventListener('mousedown', (e) => {
            const rect = c.getBoundingClientRect();
            const sx = e.clientX - rect.left;
            const sy = e.clientY - rect.top;
            const node = this.nodeAt(sx, sy);
            if (node) {
                this.dragNode = node;
                // Do NOT bump alpha — clicking a node should not restart the
                // physics simulation and scatter other nodes. Only dragging
                // physically moves this node (handled in mousemove).
            } else {
                this.isDragging = true;
            }
            this.lastMouse = { x: sx, y: sy };
        });
        c.addEventListener('mousemove', (e) => {
            const rect = c.getBoundingClientRect();
            const sx = e.clientX - rect.left;
            const sy = e.clientY - rect.top;
            if (this.dragNode) {
                const p = this.toWorld(sx, sy);
                this.dragNode.x = p.x;
                this.dragNode.y = p.y;
                this.draw();
            } else if (this.isDragging) {
                this.offsetX += sx - this.lastMouse.x;
                this.offsetY += sy - this.lastMouse.y;
                this.lastMouse = { x: sx, y: sy };
                this.draw();
            } else {
                const node = this.nodeAt(sx, sy);
                if (node !== this.hoverNode) {
                    this.hoverNode = node;
                    c.style.cursor = node ? 'pointer' : 'grab';
                    this.draw();
                }
            }
        });
        c.addEventListener('mouseup', (e) => {
            const rect = c.getBoundingClientRect();
            const sx = e.clientX - rect.left;
            const sy = e.clientY - rect.top;
            if (this.dragNode) {
                // treat as click if barely moved
                const moved = Math.hypot(sx - this.lastMouse.x, sy - this.lastMouse.y);
                this.dragNode = null;
            }
            this.isDragging = false;
        });
        c.addEventListener('click', (e) => {
            const rect = c.getBoundingClientRect();
            const sx = e.clientX - rect.left;
            const sy = e.clientY - rect.top;
            const node = this.nodeAt(sx, sy);
            if (node) {
                selectNode(node);
                this.selectedNode = node.id;
                this.draw();
                // If locked, re-lock to the clicked node (shift focus).
                if (this.locked) this.lockTo(node.id);
            }
        });
        c.addEventListener('wheel', (e) => {
            e.preventDefault();
            const rect = c.getBoundingClientRect();
            const sx = e.clientX - rect.left;
            const sy = e.clientY - rect.top;
            const factor = e.deltaY < 0 ? 1.15 : 0.87;
            const newScale = Math.min(5, Math.max(0.2, this.scale * factor));
            // zoom toward cursor
            const wx = (sx - this.offsetX) / this.scale;
            const wy = (sy - this.offsetY) / this.scale;
            this.offsetX = sx - wx * newScale;
            this.offsetY = sy - wy * newScale;
            this.scale = newScale;
            this.draw();
        }, { passive: false });
    }

    zoomBy(factor) {
        const cx = this.width / 2;
        const cy = this.height / 2;
        const newScale = Math.min(5, Math.max(0.2, this.scale * factor));
        const wx = (cx - this.offsetX) / this.scale;
        const wy = (cy - this.offsetY) / this.scale;
        this.offsetX = cx - wx * newScale;
        this.offsetY = cy - wy * newScale;
        this.scale = newScale;
        this.draw();
    }

    resetView() {
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.alpha = 0.5;
        this.start();
    }

    toggleTable(table, el) {
        if (this.hiddenTables.has(table)) {
            this.hiddenTables.delete(table);
            el.classList.remove('dim');
        } else {
            this.hiddenTables.add(table);
            el.classList.add('dim');
        }
        this.draw();
        // Re-render the detail panel so connections to hidden tables disappear.
        if (this.selectedNode && graphData && graphData._nodeById) {
            const n = graphData._nodeById[this.selectedNode];
            if (n) selectNode({ id: n.id, table: n.table, pk: n.pk, label: n.label, fields: n.fields, full_fields: n.full_fields });
        }
    }

    focusNode(nodeId) {
        // Find the node by id in the renderer's node list.
        const node = this.nodes.find(n => n.id === nodeId);
        if (!node) return;
        // Pan + zoom so the node is centered. Animate the pan smoothly without
        // restarting the physics simulation (no alpha bump, no start()).
        this.selectedNode = nodeId;
        this._animatePanTo(node.x, node.y, Math.max(this.scale, 1.8));
    }

    _animatePanTo(targetX, targetY, targetScale) {
        // Smooth animated pan/zoom to center (targetX, targetY) at targetScale.
        // Does NOT restart the force simulation — nodes stay where they are.
        const startX = this.offsetX, startY = this.offsetY, startScale = this.scale;
        const endX = this.width / 2 - targetX * targetScale;
        const endY = this.height / 2 - targetY * targetScale;
        const duration = 400; // ms
        const t0 = performance.now();
        const animate = (now) => {
            const t = Math.min(1, (now - t0) / duration);
            const ease = 1 - Math.pow(1 - t, 3); // ease-out cubic
            this.offsetX = startX + (endX - startX) * ease;
            this.offsetY = startY + (endY - startY) * ease;
            this.scale = startScale + (targetScale - startScale) * ease;
            this.draw();
            if (t < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
    }

    _computeNeighbors(nodeId) {
        // Compute the 1-hop neighbor set (including the center) from edges.
        const neighbors = new Set([nodeId]);
        for (const e of this.edges) {
            if (e.source.id === nodeId) neighbors.add(e.target.id);
            else if (e.target.id === nodeId) neighbors.add(e.source.id);
        }
        return neighbors;
    }

    _computeDeepNeighbors(nodeId) {
        // BFS/DFS: all transitively reachable nodes from the center (including
        // the center itself), following edges in both directions until no new
        // nodes are found. This reaches all leaves.
        const visited = new Set([nodeId]);
        const stack = [nodeId];
        while (stack.length) {
            const cur = stack.pop();
            for (const e of this.edges) {
                let next = null;
                if (e.source.id === cur) next = e.target.id;
                else if (e.target.id === cur) next = e.source.id;
                if (next !== null && !visited.has(next)) {
                    visited.add(next);
                    stack.push(next);
                }
            }
        }
        return visited;
    }

    toggleLock() {
        if (!this.locked) {
            // Lock to the currently selected node, or the focal node.
            const focal = this.nodes.find(n => n.isFocal);
            const center = this.selectedNode || (focal && focal.id);
            if (!center) return;
            this.lockCenter = center;
            this.lockNeighbors = this._computeNeighbors(center);
            this.locked = true;
            // Gentle reheat so neighbors approach smoothly without jumping.
            this.alpha = Math.max(this.alpha, 0.3);
            this.start();
            // Pan toward the center node (smooth, no physics restart).
            this.focusNode(center);
        } else {
            // Unlock — fade everything back.
            this.locked = false;
        }
        // Animate lockAlpha in a dedicated loop (no force simulation restart).
        this._animateLockAlpha();
    }

    toggleDeepLock() {
        // Deep lock: show the focal + ALL transitively connected descendants
        // (connected -> connected -> ... -> leaves).
        if (!this.locked) {
            const focal = this.nodes.find(n => n.isFocal);
            const center = this.selectedNode || (focal && focal.id);
            if (!center) return;
            this.lockCenter = center;
            this.lockNeighbors = this._computeDeepNeighbors(center);
            this.locked = true;
            this.alpha = Math.max(this.alpha, 0.3);
            this.start();
            this.focusNode(center);
        } else {
            this.locked = false;
        }
        this._animateLockAlpha();
    }

    _animateLockAlpha() {
        // Animate lockAlpha toward target without restarting the force sim.
        const animate = () => {
            const target = this.locked ? 1 : 0;
            if (this.lockAlpha < target) this.lockAlpha = Math.min(target, this.lockAlpha + 0.06);
            else if (this.lockAlpha > target) this.lockAlpha = Math.max(target, this.lockAlpha - 0.06);
            this.draw();
            if (Math.abs(this.lockAlpha - target) > 0.01) {
                requestAnimationFrame(animate);
            } else {
                this.lockAlpha = target;
                this.draw();
            }
        };
        requestAnimationFrame(animate);
    }

    lockTo(nodeId) {
        // Re-lock to a new center (used when clicking a node while locked).
        // The center node is pinned (see tick) so it stays put; only its
        // neighbors approach it. Gentle reheat so things don't jump.
        if (!this.nodeMap[nodeId]) return;
        this.lockCenter = nodeId;
        this.lockNeighbors = deepLockedMode
            ? this._computeDeepNeighbors(nodeId)
            : this._computeNeighbors(nodeId);
        this.selectedNode = nodeId;
        // Gentle reheat — neighbors approach without scattering.
        this.alpha = Math.max(this.alpha, 0.25);
        this.start();
        // Pan to the new center (smooth, no physics restart).
        const node = this.nodeMap[nodeId];
        this._animatePanTo(node.x, node.y, Math.max(this.scale, 1.8));
    }
}

function setupCanvasControls() {
    document.getElementById('zoom-in').addEventListener('click', () => render && render.zoomBy(1.2));
    document.getElementById('zoom-out').addEventListener('click', () => render && render.zoomBy(0.83));
    document.getElementById('reset-view').addEventListener('click', () => render && render.resetView());
}

function renderGraph(data) {
    if (!render) render = new ForceGraph('graph-canvas', 'graph-meta');
    // Build a node-by-id lookup so connection clicks are O(1) not O(n).
    data._nodeById = {};
    data.nodes.forEach(n => { data._nodeById[n.id] = n; });
    // Build edge adjacency for fast connection lookup in selectNode.
    data._edgeByNode = {};
    data.edges.forEach(e => {
        (data._edgeByNode[e.source] = data._edgeByNode[e.source] || []).push({ edge: e, dir: 'out' });
        (data._edgeByNode[e.target] = data._edgeByNode[e.target] || []).push({ edge: e, dir: 'in' });
    });
    // Legend scoped to tables present in this graph, with counts
    const counts = {};
    data.nodes.forEach(n => { counts[n.table] = (counts[n.table] || 0) + 1; });
    const presentTables = Object.keys(counts).sort().map(name => ({
        name, color: data.colors[name] || '#888', row_count: counts[name]
    }));
    renderLegend(presentTables, counts);

    render.setData(data);
    document.getElementById('graph-meta').textContent =
        `graph ${data.graph_id} · ${data.graph_size} nodes · showing ${data.rendered_count}` +
        (data.truncated ? ' (capped)' : '') + ` · flow ${data.flow_id}`;

    // Default detail: focal node
    const focal = data.nodes.find(n => n.is_focal);
    if (focal) selectNode({ id: focal.id, table: focal.table, pk: focal.pk, label: focal.label, fields: focal.fields, full_fields: focal.full_fields });
    else clearDetail();
}

function clearGraph() {
    if (render) { render.nodes = []; render.edges = []; render.draw(); }
    document.getElementById('graph-meta').textContent = '';
    clearDetail();
    document.getElementById('legend-items').innerHTML =
        '<div class="legend-empty">Select a dataset and id to see the legend.</div>';
}

// Generic bookkeeping / noise columns to hide in the detail panel by default.
// These are common across schemas and add no semantic value when inspecting a
// node. The user can still expand "Show all fields" to see them. Additional
// noise fields can be specified per-schema via options.noise_fields in the YAML.
const NOISE_FIELDS = new Set([
    'created_at', 'updated_at', 'created_time', 'last_edited_time',
    'is_title', 'is_inline', 'is_archived', 'in_trash', 'is_skill',
    'is_primary', 'selected', 'hidden', 'deleted', 'position', 'ordinal',
    'history_id_last', 'sequence', 'internal_date_ms', 'size_estimate',
    'messages_total', 'threads_total', 'messages_unread', 'threads_unread',
]);

function getNoiseFields() {
    // Merge the hardcoded defaults with any noise_fields declared in the
    // current dataset's schema options (YAML-driven, schema-specific).
    const combined = new Set(NOISE_FIELDS);
    if (schema && schema.options && Array.isArray(schema.options.noise_fields)) {
        schema.options.noise_fields.forEach(f => combined.add(f));
    }
    return combined;
}

function selectNode(node) {
    const detail = document.getElementById('detail-content');
    const color = (graphData && graphData.colors && graphData.colors[node.table]) || '#888';
    const fields = node.fields || {};
    const allKeys = Object.keys(fields);

    // Find connections of this node from the cached edge adjacency.
    // Skip connections to/from tables hidden via the legend filter.
    let connections = [];
    if (graphData && graphData._edgeByNode) {
        const hidden = render ? render.hiddenTables : new Set();
        const adj = graphData._edgeByNode[node.id] || [];
        for (const { edge: e, dir } of adj) {
            if (dir === 'out') {
                const tgt = graphData._nodeById[e.target];
                if (tgt && !hidden.has(tgt.table))
                    connections.push({ field: e.field, to_table: tgt.table, to_pk: tgt.pk, label: tgt.label, id: e.target });
            } else {
                const src = graphData._nodeById[e.source];
                if (src && !hidden.has(src.table))
                    connections.push({ field: e.field, to_table: src.table, to_pk: src.pk, label: src.label, id: e.source, reverse: true });
            }
        }
    }

    // Show ALL fields — no noise/primary split, nothing hidden.
    const labelField = (graphData && graphData.hint_fields && graphData.hint_fields[node.table]) || null;
    const fieldKeys = [];
    for (const k of allKeys) {
        const v = fields[k];
        if (v === '' || v === null || v === undefined) continue;
        fieldKeys.push(k);
    }
    // If the row has no id/pk field of its own, surface the pk as a clear "id" field.
    const hasIdField = fieldKeys.some(k => k === 'id' || k === 'pk');
    const idLeadRow = hasIdField ? '' : `
        <div class="detail-field detail-field-id">
            <span class="k">id</span>
            <span class="v">${escapeHtml(String(node.pk ?? ''))}</span>
        </div>`;
    // sort: put id/pk first, then alphabetical
    fieldKeys.sort((a, b) => {
        const aIsId = (a === 'id' || a === 'pk') ? 0 : 1;
        const bIsId = (b === 'id' || b === 'pk') ? 0 : 1;
        if (aIsId !== bIsId) return aIsId - bIsId;
        return a.localeCompare(b);
    });

    const fullFields = node.full_fields || {};
    const renderFieldRow = (k) => {
        const display = String(fields[k] ?? '');
        const full = fullFields[k];
        const isLabel = (k === labelField);
        const labelBadge = isLabel ? '<span class="field-badge" title="This field is used as the node name">name</span>' : '';
        const cls = isLabel ? 'detail-field detail-field-label' : 'detail-field';
        if (full) {
            return `
        <div class="${cls}">
            <span class="k">${escapeHtml(k)}${labelBadge}</span>
            <span class="v detail-field-truncated" data-full="${escapeAttr(full)}" title="Click to see full value">${escapeHtml(display)}</span>
        </div>`;
        }
        return `
        <div class="${cls}">
            <span class="k">${escapeHtml(k)}${labelBadge}</span>
            <span class="v">${escapeHtml(display)}</span>
        </div>`;
    };

    const fieldRows = fieldKeys.length ? fieldKeys.map(renderFieldRow).join('') : '';
    const labelHint = labelField ? `<span class="label-field-hint" title="Node name comes from this field">${escapeHtml(labelField)}</span>` : '';

    detail.innerHTML = `
        <div class="detail-title">${escapeHtml(node.label || node.pk)}${labelHint}</div>
        <div class="detail-subtitle">
            <span class="table-tag" style="background:${color}40;color:${color}">${escapeHtml(node.table)}</span>
            <span>${escapeHtml(node.pk)}</span>
        </div>
        <div class="detail-fields">
            ${idLeadRow}${fieldRows}${(!fieldRows && !idLeadRow) ? '<div class="detail-empty">No fields.</div>' : ''}
        </div>
        ${connections.length ? `
            <div class="detail-connections">
                <h4>Connections (${connections.length})</h4>
                ${connections.map(c => `
                    <div class="conn-item" data-id="${escapeAttr(c.id)}">
                        <span class="field-name">${escapeHtml(c.field)}</span>
                        ${c.reverse ? '←' : '→'}
                        <span style="color:${(graphData.colors[c.to_table] || '#888')}">●</span>
                        ${escapeHtml(c.to_table)}/${escapeHtml(truncate(c.label || c.to_pk, 30))}
                    </div>`).join('')}
            </div>` : ''}
    `;

    // Click truncated field values to see the full value in a popup.
    detail.querySelectorAll('.detail-field-truncated').forEach(el => {
        el.addEventListener('click', () => {
            const full = el.dataset.full;
            if (!full) return;
            showFieldPopup(el, full);
        });
    });

    detail.querySelectorAll('.conn-item').forEach(el => {
        el.addEventListener('click', () => {
            const target = graphData && graphData._nodeById ? graphData._nodeById[el.dataset.id] : null;
            if (target) {
                selectNode({ id: target.id, table: target.table, pk: target.pk, label: target.label, fields: target.fields, full_fields: target.full_fields });
                // Navigate to the node in the graph: pan + zoom + highlight.
                if (render) {
                    render.selectedNode = target.id;
                    render.draw();
                    render.focusNode(target.id);
                    // If locked, re-lock to the clicked node (shift focus).
                    if (render.locked) render.lockTo(target.id);
                }
            }
        });
    });
}

function clearDetail() {
    document.getElementById('detail-content').innerHTML =
        '<div class="detail-empty">Click a node to inspect its data.</div>';
}

function showFieldPopup(srcEl, fullValue) {
    // Remove any existing field popup.
    const existing = document.getElementById('field-popup');
    if (existing) existing.remove();

    const popup = document.createElement('div');
    popup.id = 'field-popup';
    popup.className = 'field-popup';
    popup.innerHTML = `
        <div class="field-popup-card">
            <div class="field-popup-header">
                <span>Full value</span>
                <div class="field-popup-actions">
                    <button type="button" class="field-popup-copy">Copy</button>
                    <button type="button" class="field-popup-close">✕</button>
                </div>
            </div>
            <pre class="field-popup-body">${escapeHtml(fullValue)}</pre>
        </div>`;

    document.body.appendChild(popup);

    const close = () => popup.remove();
    popup.querySelector('.field-popup-close').addEventListener('click', close);
    popup.querySelector('.field-popup-copy').addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(fullValue);
            popup.querySelector('.field-popup-copy').textContent = 'Copied!';
            setTimeout(() => { popup.querySelector('.field-popup-copy').textContent = 'Copy'; }, 1500);
        } catch {
            const ta = document.createElement('textarea');
            ta.value = fullValue;
            document.body.appendChild(ta); ta.select();
            try { document.execCommand('copy'); popup.querySelector('.field-popup-copy').textContent = 'Copied!'; setTimeout(() => { popup.querySelector('.field-popup-copy').textContent = 'Copy'; }, 1500); } catch {}
            document.body.removeChild(ta);
        }
    });
    // Click outside closes.
    popup.addEventListener('click', (e) => { if (e.target === popup) close(); });
    // Esc closes.
    const escHandler = (e) => { if (e.key === 'Escape') { close(); document.removeEventListener('keydown', escHandler); } };
    document.addEventListener('keydown', escHandler);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function showStatus(el, msg, type) {
    if (!el) return;
    el.textContent = msg;
    el.className = 'status-message ' + type;
}

function lockLabel() {
    if (deepLockedMode) return ', deep locked';
    if (lockedMode) return ', locked';
    return '';
}

function reapplyLock() {
    if (!render) return;
    if (deepLockedMode) render.toggleDeepLock();
    else if (lockedMode) render.toggleLock();
}

function showSection(id) {
    document.getElementById(id).style.display = 'block';
}

function closeSection(id) {
    document.getElementById(id).style.display = 'none';
}

function escapeHtml(s) {
    const a = String.fromCharCode(38); // &
    const map = {};
    map['&'] = a + 'amp;';
    map['<'] = a + 'lt;';
    map['>'] = a + 'gt;';
    map['"'] = a + 'quot;';
    map["'"] = a + '#39;';
    return String(s).replace(/[&<>"']/g, c => map[c]);
}

function escapeAttr(s) {
    return escapeHtml(s);
}

function truncate(s, n) {
    s = String(s);
    return s.length > n ? s.slice(0, n) + '…' : s;
}
