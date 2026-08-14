// Graph Visualizer JavaScript

let currentDataset = null;
let schema = null;          // {tables, colors, hint_fields, types, options}
let graphData = null;       // last rendered graph payload
let render = null;          // ForceGraph renderer instance

const API = '/clone/graph_visualizer';

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
        const res = await fetch(`${API}/datasets`);
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
                Graphs: ${d.summary.graphs || 0} &middot; Types: ${d.summary.types || 0}<br>
                Largest graph: ${d.summary.largest_graph || 0} nodes
            </div>
            <div class="db-actions">
                <button class="mini-btn" data-act="visualize">Visualize</button>
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
        const res = await fetch(`${API}/upload`, { method: 'POST', body: fd });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            throw new Error(data.message || 'Upload failed');
        }
        showStatus(status,
            `Dataset "${data.name}" created. Tables: ${data.summary.tables}, ` +
            `Rows: ${data.summary.rows}, Graphs: ${data.summary.graphs}, ` +
            `Types: ${data.summary.types}.`, 'success');
        await loadDatasets();
        openVisualizer(data.dataset_id);
    } catch (e) {
        showStatus(status, e.message, 'error');
    } finally {
        document.getElementById('upload-btn').disabled = false;
    }
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
        const idSel = document.getElementById('id-select');
        idSel.innerHTML = '<option value="">Loading...</option>';
        if (!table) {
            idSel.innerHTML = '<option value="">-- Select a table first --</option>';
            document.getElementById('visualize-btn').disabled = true;
            return;
        }
        await loadIds(table);
    });

    document.getElementById('type-select').addEventListener('change', async () => {
        const table = document.getElementById('table-select').value;
        if (table) await loadIds(table);
    });

    document.getElementById('visualize-btn').addEventListener('click', visualize);
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
        const res = await fetch(`${API}/schema/${datasetId}`);
        const data = await res.json();
        if (data.status !== 'success') throw new Error(data.message);

        schema = data;

        // Type dropdown
        const typeSel = document.getElementById('type-select');
        typeSel.innerHTML = '<option value="">All types</option>' +
            (data.types || []).map(t => `
                <option value="${t.type_id}">Type ${t.type_id} — ${t.tables.join(', ')} (${t.count})</option>
            `).join('');

        // Table dropdown
        const tableSel = document.getElementById('table-select');
        tableSel.innerHTML = '<option value="">-- Select a table --</option>' +
            data.tables.map(t => `
                <option value="${t.name}">${t.name} (${t.row_count})</option>
            `).join('');

        // Legend (full color legend for all tables)
        renderLegend(data.tables, null);

        // Reset id select
        document.getElementById('id-select').innerHTML =
            '<option value="">-- Select a table first --</option>';
        document.getElementById('visualize-btn').disabled = true;
        clearGraph();
        showStatus(status, `Loaded schema for "${data.name}".`, 'success');
    } catch (e) {
        showStatus(status, e.message, 'error');
    }
}

async function loadIds(table) {
    const typeId = document.getElementById('type-select').value;
    const idSel = document.getElementById('id-select');
    const url = `${API}/ids/${currentDataset}?table=${encodeURIComponent(table)}` +
        (typeId ? `&type=${typeId}` : '');
    try {
        const res = await fetch(url);
        const data = await res.json();
        if (data.status !== 'success') throw new Error(data.message);

        idSel.innerHTML = `<option value="">-- Select an id (${data.count} available) --</option>` +
            data.ids.map(i => {
                const label = i.label ? `${i.label}` : i.pk;
                return `<option value="${escapeAttr(i.pk)}" data-graph="${i.graph_id}" data-size="${i.graph_size}" data-type="${i.type_id}">${escapeHtml(label)} — ${escapeHtml(i.pk)} (graph ${i.graph_id}, ${i.graph_size})</option>`;
            }).join('');
        document.getElementById('visualize-btn').disabled = (data.ids.length === 0);
    } catch (e) {
        idSel.innerHTML = '<option value="">-- error --</option>';
    }
}

async function visualize() {
    const table = document.getElementById('table-select').value;
    const id = document.getElementById('id-select').value;
    const status = document.getElementById('load-status');
    if (!table || !id) {
        showStatus(status, 'Select both a table and an id.', 'error');
        return;
    }
    showStatus(status, 'Loading graph...', 'info');
    try {
        const res = await fetch(`${API}/graph/${currentDataset}?table=${encodeURIComponent(table)}&id=${encodeURIComponent(id)}`);
        const data = await res.json();
        if (data.status !== 'success') throw new Error(data.message);

        graphData = data;
        renderGraph(data);
        showStatus(status,
            `Graph ${data.graph_id}: ${data.graph_size} connected nodes ` +
            `(showing ${data.rendered_count}${data.truncated ? ', capped' : ''}, type ${data.type_id}).`,
            'success');
    } catch (e) {
        showStatus(status, e.message, 'error');
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
        // Centering + integrate
        const cx = this.width / 2;
        const cy = this.height / 2;
        for (const a of nodes) {
            if (a === this.dragNode) { a.vx = 0; a.vy = 0; continue; }
            a.vx += (cx - a.x) * 0.005 * this.alpha;
            a.vy += (cy - a.y) * 0.005 * this.alpha;
            a.vx *= 0.82; a.vy *= 0.82;
            a.x += a.vx; a.y += a.vy;
        }
        this.alpha *= 0.992;
        this.draw();
        if (this.alpha < 0.005) { this.running = false; this.draw(); return; }
        requestAnimationFrame(this.tick);
    }

    draw() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.width, this.height);
        ctx.save();
        ctx.translate(this.offsetX, this.offsetY);
        ctx.scale(this.scale, this.scale);

        // Edges
        ctx.lineWidth = 1 / this.scale;
        ctx.strokeStyle = 'rgba(255,255,255,0.18)';
        for (const e of this.edges) {
            if (this.hiddenTables.has(e.source.table) || this.hiddenTables.has(e.target.table)) continue;
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
            const r = n.r * (n.isFocal ? 1.4 : 1) * (isHover ? 1.4 : 1);

            ctx.beginPath();
            ctx.arc(n.x, n.y, r, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            if (n.isFocal) {
                ctx.lineWidth = 3 / this.scale;
                ctx.strokeStyle = '#ffffff';
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

            // Label for focal / large enough graphs
            if (n.isFocal || this.scale > 1.4 || isHover) {
                ctx.fillStyle = 'rgba(255,255,255,0.9)';
                ctx.font = `${11 / this.scale}px sans-serif`;
                ctx.textAlign = 'center';
                ctx.fillText(truncate(n.label, 24), n.x, n.y - r - 3 / this.scale);
            }
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
                this.alpha = Math.max(this.alpha, 0.3);
                this.start();
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
            if (node) selectNode(node);
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
    }
}

function setupCanvasControls() {
    document.getElementById('zoom-in').addEventListener('click', () => render && render.zoomBy(1.2));
    document.getElementById('zoom-out').addEventListener('click', () => render && render.zoomBy(0.83));
    document.getElementById('reset-view').addEventListener('click', () => render && render.resetView());
}

function renderGraph(data) {
    if (!render) render = new ForceGraph('graph-canvas', 'graph-meta');
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
        (data.truncated ? ' (capped)' : '') + ` · type ${data.type_id}`;

    // Default detail: focal node
    const focal = data.nodes.find(n => n.is_focal);
    if (focal) selectNode({ id: focal.id, table: focal.table, pk: focal.pk, label: focal.label, fields: focal.fields });
    else clearDetail();
}

function clearGraph() {
    if (render) { render.nodes = []; render.edges = []; render.draw(); }
    document.getElementById('graph-meta').textContent = '';
    clearDetail();
    document.getElementById('legend-items').innerHTML =
        '<div class="legend-empty">Select a dataset and id to see the legend.</div>';
}

function selectNode(node) {
    const detail = document.getElementById('detail-content');
    const color = (graphData && graphData.colors && graphData.colors[node.table]) || '#888';
    const fields = node.fields || {};
    const fieldKeys = Object.keys(fields);

    // Find connections of this node from graphData edges
    let connections = [];
    if (graphData) {
        for (const e of graphData.edges) {
            if (e.source === node.id) {
                const tgt = graphData.nodes.find(n => n.id === e.target);
                if (tgt) connections.push({ field: e.field, to_table: tgt.table, to_pk: tgt.pk, label: tgt.label, id: e.target });
            } else if (e.target === node.id) {
                const src = graphData.nodes.find(n => n.id === e.source);
                if (src) connections.push({ field: e.field, to_table: src.table, to_pk: src.pk, label: src.label, id: e.source, reverse: true });
            }
        }
    }

    detail.innerHTML = `
        <div class="detail-title">${escapeHtml(node.label || node.pk)}</div>
        <div class="detail-subtitle">
            <span class="table-tag" style="background:${color}40;color:${color}">${escapeHtml(node.table)}</span>
            <span>${escapeHtml(node.pk)}</span>
        </div>
        <div class="detail-fields">
            ${fieldKeys.length ? fieldKeys.map(k => `
                <div class="detail-field">
                    <span class="k">${escapeHtml(k)}</span>
                    <span class="v">${escapeHtml(String(fields[k] ?? ''))}</span>
                </div>`).join('') : '<div class="detail-empty">No fields.</div>'}
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

    detail.querySelectorAll('.conn-item').forEach(el => {
        el.addEventListener('click', () => {
            const target = graphData.nodes.find(n => n.id === el.dataset.id);
            if (target) selectNode({ id: target.id, table: target.table, pk: target.pk, label: target.label, fields: target.fields });
        });
    });
}

function clearDetail() {
    document.getElementById('detail-content').innerHTML =
        '<div class="detail-empty">Click a node to inspect its data.</div>';
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function showStatus(el, msg, type) {
    if (!el) return;
    el.textContent = msg;
    el.className = 'status-message ' + type;
}

function showSection(id) {
    document.getElementById(id).style.display = 'block';
}

function closeSection(id) {
    document.getElementById(id).style.display = 'none';
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
        '&': '&', '<': '<', '>': '>', '"': '"', "'": '&#39;'
    }[c]));
}

function escapeAttr(s) {
    return escapeHtml(s);
}

function truncate(s, n) {
    s = String(s);
    return s.length > n ? s.slice(0, n) + '…' : s;
}
