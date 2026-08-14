"""
graph_visualizer.py

A Flask blueprint that turns a zipped seed .sql file + a YAML schema/connections
file into an interactive connected-components graph visualizer.

Pipeline (generic - no schema is hardcoded; everything is driven by the YAML):
  1. Parse the YAML (tables, primary keys, foreign-key edges, containment
     hierarchy, references, hint fields, options like exclude_hubs).
  2. Parse the seed .sql (PostgreSQL-style INSERT INTO "t" ("cols") VALUES ...).
     Every row of every table becomes a node (identity = table + primary key).
  3. Every foreign-key edge is an undirected graph edge. Connected components are
     the "graphs". Optional `exclude_hubs` drops INCOMING edges to hub tables so a
     hub does not collapse the whole dataset into one giant component.
  4. Each graph is assigned a structural "type" (tables present + root tables +
     containment edge types) so the UI can filter by type.
  5. Endpoints expose datasets, schema (tables/colors), graphs, ids per table, and
     the component (nodes + edges + fields) for a chosen (table, id).

The frontend renders a force-directed graph, colours nodes by table, shows a
legend, and displays a node's data on click.
"""

import os
import re
import json
import uuid
import zipfile
import tempfile
from datetime import datetime

import yaml
from flask import Blueprint, render_template, request, jsonify, abort

graph_visualizer_bp = Blueprint('graph_visualizer', __name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_visualizer_data")
os.makedirs(DATA_DIR, exist_ok=True)

# In-memory cache of processed datasets, keyed by dataset_id.
_DATASETS = {}

# A curated palette of distinct colours. Assigned to tables in sorted order so the
# same dataset always renders with the same colours across reloads.
COLOR_PALETTE = [
    "#ef4444", "#f97316", "#f59e0b", "#eab308", "#84cc16", "#22c55e",
    "#10b981", "#14b8a6", "#06b6d4", "#0ea5e9", "#3b82f6", "#6366f1",
    "#8b5cf6", "#a855f7", "#d946ef", "#ec4899", "#f43f5e", "#64748b",
    "#94a3b8", "#cbd5e1", "#fbbf24", "#a3e635", "#5eead4", "#60a5fa",
    "#c084fc", "#fb7185", "#34d399", "#facc15", "#38bdf8", "#f472b6",
]

HEADER_RE = re.compile(r'INSERT INTO "(\w+)" \(([^)]*)\)\s*VALUES\s*$')


# ---------------------------------------------------------------------------
# YAML schema loading
# ---------------------------------------------------------------------------

def _normalize_pk(pk):
    if isinstance(pk, list):
        return tuple(pk)
    return pk


def _load_schema(yaml_text):
    """Parse the YAML schema file into a normalized dict."""
    data = yaml.safe_load(yaml_text)
    if not data or "tables" not in data:
        raise ValueError("YAML must contain a top-level 'tables' mapping")

    tables = {}
    for name, meta in data["tables"].items():
        pk = _normalize_pk(meta.get("pk"))
        if not pk:
            raise ValueError(f"Table '{name}' is missing a primary key (pk)")
        columns = list(meta.get("columns", []))
        edges = []
        for e in meta.get("edges", []) or []:
            edges.append({
                "column": e["column"],
                "to_table": e["to_table"],
                "to_pk": e["to_pk"],
                "conditional": bool(e.get("conditional", False)),
            })
        tables[name] = {
            "pk": pk,
            "columns": columns,
            "edges": edges,
            "email_join": meta.get("email_join"),
        }

    options = data.get("options", {}) or {}
    schema = {
        "name": data.get("name", "dataset"),
        "description": data.get("description", ""),
        "version": data.get("version", 1),
        "options": {
            "max_field_len": int(options.get("max_field_len", 120)),
            "exclude_hubs": list(options.get("exclude_hubs", []) or []),
        },
        "tables": tables,
        "hierarchy": [list(h) if not isinstance(h, dict) else h
                      for h in (data.get("hierarchy", []) or [])],
        "references": [list(r) if not isinstance(r, dict) else r
                       for r in (data.get("references", []) or [])],
        "hint_fields": dict(data.get("hint_fields", {}) or {}),
    }
    return schema


def _assign_colors(tables):
    colors = {}
    for i, name in enumerate(sorted(tables.keys())):
        colors[name] = COLOR_PALETTE[i % len(COLOR_PALETTE)]
    return colors


# ---------------------------------------------------------------------------
# SQL value parsing (find-based; leaps over huge base64 / multi-line strings)
# ---------------------------------------------------------------------------

def _find_string_end(text, start):
    i = start + 1
    n = len(text)
    while i < n:
        j = text.find("'", i)
        if j == -1:
            return -1
        if j + 1 < n and text[j + 1] == "'":
            i = j + 2
            continue
        return j + 1
    return -1


def _scan_balance(text, in_str, depth):
    i = 0
    n = len(text)
    while i < n:
        if in_str:
            j = text.find("'", i)
            if j == -1:
                return in_str, depth
            if j + 1 < n and text[j + 1] == "'":
                i = j + 2
                continue
            in_str = False
            i = j + 1
        else:
            c = text[i]
            if c == "'":
                in_str = True
                i += 1
            elif c == "(":
                depth += 1
                i += 1
            elif c == ")":
                depth -= 1
                i += 1
            else:
                i += 1
    return in_str, depth


def _clean(val):
    v = val.strip()
    if v == "NULL":
        return None
    if len(v) >= 2 and v[0] == "'" and v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return v


def _truncate(v, max_len):
    if v is None:
        return ""
    s = str(v)
    if len(s) > max_len:
        return s[:max_len] + f"...(+{len(s) - max_len} chars)"
    return s


def _extract_all_values(text):
    """Parse the first tuple in *text* and return ALL column values (cleaned).
    Returns (values_list, ok) where ok is False if the tuple did not close on text."""
    p = text.find("(")
    if p == -1:
        return [], False
    i = p + 1
    n = len(text)
    depth = 1
    in_str = False
    result = []
    val_start = i
    while i < n:
        if in_str:
            j = text.find("'", i)
            if j == -1:
                return result, False
            if j + 1 < n and text[j + 1] == "'":
                i = j + 2
                continue
            in_str = False
            i = j + 1
        else:
            c = text[i]
            if c == "'":
                in_str = True
                i += 1
            elif c == "(":
                depth += 1
                i += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    result.append(_clean(text[val_start:i]))
                    return result, True
                i += 1
            elif c == "," and depth == 1:
                result.append(_clean(text[val_start:i]))
                i += 1
                val_start = i
            else:
                i += 1
    return result, False


# ---------------------------------------------------------------------------
# SQL -> nodes + connections
# ---------------------------------------------------------------------------

def _parse_sql(sql_text, schema):
    """Parse the seed SQL using the YAML schema. Returns (nodes, row_counts).

    nodes: dict key -> {table, pk, pk_display, label, fields, connections}
    row_counts: dict table -> number of real rows
    """
    max_len = schema["options"]["max_field_len"]
    tables = schema["tables"]
    hint_fields = schema["hint_fields"]
    nodes = {}
    row_counts = {t: 0 for t in tables}

    # Sets to resolve conditional edges (only follow when target is a real row).
    real_id_sets = {t: set() for t in tables}      # table -> {pk_value}
    email_map = {}                                  # email -> user pk (for email_join)

    # First pass: collect every real primary-key value per table (so conditional
    # edges can be resolved deterministically). We re-scan headers quickly.
    # We do two passes over the file text: pass 1 fills real_id_sets, pass 2 builds
    # nodes. This is simpler than deferring edges and handles email joins cleanly.
    lines = sql_text.splitlines(keepends=False)

    def iter_rows():
        """Yield (table, col_names, col_index, values) for every data tuple."""
        cur_table = None
        col_names = []
        col_index = {}
        it = iter(lines)
        for line in it:
            if line.startswith("INSERT INTO"):
                m = HEADER_RE.match(line)
                if not m:
                    cur_table = None
                    continue
                tname = m.group(1)
                if tname not in tables:
                    cur_table = None
                    continue
                cur_table = tname
                col_names = [c.strip().strip('"') for c in m.group(2).split(",")]
                col_index = {name: i for i, name in enumerate(col_names)}
                continue
            if cur_table is None:
                continue
            stripped = line.lstrip()
            if stripped == "" or stripped.startswith("--"):
                continue
            if not stripped.startswith("("):
                continue
            vals, ok = _extract_all_values(line)
            if not ok:
                buf = [line]
                in_str, depth = _scan_balance(line, False, 0)
                while in_str or depth > 0:
                    try:
                        nxt = next(it)
                    except StopIteration:
                        break
                    buf.append(nxt)
                    in_str, depth = _scan_balance(nxt, in_str, depth)
                vals, ok = _extract_all_values("\n".join(buf))
            if not ok or len(vals) < len(col_names):
                continue
            yield cur_table, col_names, col_index, vals

    # Pass 1: real id sets + email map
    for tname, col_names, col_index, vals in iter_rows():
        meta = tables[tname]
        pk = meta["pk"]
        if isinstance(pk, tuple):
            pk_parts = [vals[col_index[c]] for c in pk if c in col_index]
            if any(p is None for p in pk_parts):
                continue
            real_id_sets[tname].add("|".join(pk_parts))
        else:
            if pk not in col_index:
                continue
            pk_val = vals[col_index[pk]]
            if pk_val is None:
                continue
            real_id_sets[tname].add(pk_val)
        if tname == "users" and "email" in col_index:
            em = vals[col_index["email"]]
            if isinstance(pk, tuple):
                email_map[em] = "|".join(vals[col_index[c]] for c in pk)
            else:
                email_map[em] = vals[col_index[pk]]

    # Pass 2: build nodes + connections
    for tname, col_names, col_index, vals in iter_rows():
        meta = tables[tname]
        pk = meta["pk"]

        if isinstance(pk, tuple):
            pk_parts = [vals[col_index[c]] for c in pk if c in col_index]
            if any(p is None for p in pk_parts):
                continue
            pk_display = "|".join(pk_parts)
        else:
            if pk not in col_index:
                continue
            pk_val = vals[col_index[pk]]
            if pk_val is None:
                continue
            pk_display = pk_val

        key = f"{tname}||{pk_display}"

        # Build truncated field dict (only this table's declared columns).
        declared = meta["columns"] or col_names
        fields = {}
        for c in declared:
            if c in col_index and col_index[c] < len(vals):
                fields[c] = _truncate(vals[col_index[c]], max_len)

        # Label: hint field if present, else pk.
        hf = hint_fields.get(tname)
        label = fields.get(hf) if hf else None
        if not label:
            label = pk_display
        if len(str(label)) > 60:
            label = str(label)[:60] + "..."

        # Connections (outgoing FK references from this row).
        connections = []
        for e in meta["edges"]:
            if e["column"] not in col_index:
                continue
            fv = vals[col_index[e["column"]]]
            if fv is None or fv == "":
                continue
            tgt_table = e["to_table"]
            if e["conditional"]:
                if tgt_table not in real_id_sets:
                    continue
                if fv not in real_id_sets[tgt_table]:
                    continue
            tgt_key = f"{tgt_table}||{fv}"
            connections.append({
                "field": e["column"],
                "to_table": tgt_table,
                "to_pk": fv,
                "target_key": tgt_key,
                "conditional": e["conditional"],
            })

        # email join (non-FK): a column whose value is an email matching users.email
        ej = meta["email_join"]
        if ej and ej in col_index:
            em = vals[col_index[ej]]
            if em and em in email_map:
                uid = email_map[em]
                connections.append({
                    "field": ej,
                    "to_table": "users",
                    "to_pk": uid,
                    "target_key": f"users||{uid}",
                    "conditional": True,
                })

        nodes[key] = {
            "table": tname,
            "pk": pk_display,
            "label": label,
            "fields": fields,
            "connections": connections,
        }
        row_counts[tname] += 1

    return nodes, row_counts


# ---------------------------------------------------------------------------
# Connected components (union-find) + graph typing
# ---------------------------------------------------------------------------

def _build_components(nodes, schema):
    """Assign each real node to a connected component. Returns:
       key_to_graph, graph_members, graph_types, types_list
    """
    exclude_hubs = set(schema["options"].get("exclude_hubs", []))

    parent = {}

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for key in nodes:
        parent[key] = key

    edges_followed = 0
    for key, node in nodes.items():
        for conn in node["connections"]:
            tgt = conn["target_key"]
            if tgt not in parent:
                continue  # dangling FK -> phantom node; skip
            if conn["to_table"] in exclude_hubs:
                continue  # drop INCOMING edge to a hub table
            union(key, tgt)
            edges_followed += 1

    # Group members by root.
    root_members = {}
    for key in nodes:
        r = find(key)
        root_members.setdefault(r, []).append(key)

    # Order components: largest first, then by first member.
    comps = sorted(root_members.items(),
                   key=lambda kv: (-len(kv[1]), kv[1][0]))
    key_to_graph = {}
    graph_members = {}
    for gid, (root, members) in enumerate(comps, start=1):
        graph_members[gid] = members
        for k in members:
            key_to_graph[k] = gid

    # Type each graph by structural signature.
    hierarchy = schema["hierarchy"]
    type_of = {}
    types_list = []
    sig_index = {}

    for gid, members in graph_members.items():
        member_set = set(members)
        tables_present = sorted({nodes[k]["table"] for k in members})

        is_child = set()
        edge_types = set()
        for h in hierarchy:
            ptable, ctable, fk = h["parent"], h["child"], h["fk"]
            for k in members:
                node = nodes[k]
                if node["table"] != ctable:
                    continue
                fv = node["fields"].get(fk)
                if not fv:
                    continue
                is_child.add((node["table"], node["pk"]))
                edge_types.add((ptable, ctable))

        root_tables = sorted({
            nodes[k]["table"] for k in members
            if (nodes[k]["table"], nodes[k]["pk"]) not in is_child
        })
        sig = (tuple(tables_present), tuple(root_tables), tuple(sorted(edge_types)))
        if sig not in sig_index:
            tid = len(types_list) + 1
            sig_index[sig] = tid
            types_list.append({
                "type_id": tid,
                "tables": list(tables_present),
                "root_tables": list(root_tables),
                "edges": [list(e) for e in sorted(edge_types)],
                "count": 0,
                "graph_ids": [],
            })
        tid = sig_index[sig]
        type_of[gid] = tid
        t = types_list[tid - 1]
        t["count"] += 1
        t["graph_ids"].append(gid)

    return key_to_graph, graph_members, type_of, types_list, edges_followed


# ---------------------------------------------------------------------------
# Dataset persistence
# ---------------------------------------------------------------------------

def _dataset_dir(dataset_id):
    return os.path.join(DATA_DIR, dataset_id)


def _save_dataset(dataset_id, processed):
    d = _dataset_dir(dataset_id)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "processed.json"), "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False)
    _DATASETS[dataset_id] = processed


def _load_dataset(dataset_id):
    if dataset_id in _DATASETS:
        return _DATASETS[dataset_id]
    path = os.path.join(_dataset_dir(dataset_id), "processed.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        processed = json.load(f)
    _DATASETS[dataset_id] = processed
    return processed


def _list_datasets():
    out = []
    if not os.path.isdir(DATA_DIR):
        return out
    for name in sorted(os.listdir(DATA_DIR)):
        p = os.path.join(DATA_DIR, name, "processed.json")
        if not os.path.exists(p):
            continue
        pr = _load_dataset(name)
        if pr:
            out.append({
                "id": name,
                "name": pr.get("name", name),
                "created_at": pr.get("created_at"),
                "summary": pr.get("summary", {}),
            })
    return out


# ---------------------------------------------------------------------------
# Blueprint routes
# ---------------------------------------------------------------------------

@graph_visualizer_bp.route('/graph_visualizer', strict_slashes=False, methods=['GET'])
def graph_visualizer():
    return render_template('graph_visualizer.html')


@graph_visualizer_bp.route('/graph_visualizer/datasets', methods=['GET'])
def datasets_route():
    return jsonify({"status": "success", "datasets": _list_datasets()})


@graph_visualizer_bp.route('/graph_visualizer/schema/<dataset_id>', methods=['GET'])
def schema_route(dataset_id):
    pr = _load_dataset(dataset_id)
    if not pr:
        return jsonify({"status": "error", "message": "Dataset not found"}), 404
    tables = []
    for name in sorted(pr["tables"].keys()):
        meta = pr["tables"][name]
        tables.append({
            "name": name,
            "pk": meta["pk"] if isinstance(meta["pk"], str) else list(meta["pk"]),
            "columns": meta["columns"],
            "color": pr["colors"][name],
            "row_count": pr["summary"]["rows_per_table"].get(name, 0),
        })
    return jsonify({
        "status": "success",
        "name": pr["name"],
        "tables": tables,
        "colors": pr["colors"],
        "hint_fields": pr["hint_fields"],
        "types": pr["types"],
        "options": pr["options"],
    })


@graph_visualizer_bp.route('/graph_visualizer/graphs/<dataset_id>', methods=['GET'])
def graphs_route(dataset_id):
    pr = _load_dataset(dataset_id)
    if not pr:
        return jsonify({"status": "error", "message": "Dataset not found"}), 404
    graphs = []
    for gid, meta in sorted(pr["graphs"].items(), key=lambda kv: int(kv[0])):
        graphs.append({
            "graph_id": int(gid),
            "size": meta["size"],
            "type_id": meta["type_id"],
            "tables": meta["tables"],
        })
    return jsonify({"status": "success", "graphs": graphs})


@graph_visualizer_bp.route('/graph_visualizer/ids/<dataset_id>', methods=['GET'])
def ids_route(dataset_id):
    """List ids for a table (for the id dropdown). Optionally filter by graph type."""
    pr = _load_dataset(dataset_id)
    if not pr:
        return jsonify({"status": "error", "message": "Dataset not found"}), 404
    table = request.args.get("table")
    type_id = request.args.get("type")
    limit = min(int(request.args.get("limit", 2000)), 5000)

    if not table:
        return jsonify({"status": "error", "message": "table is required"}), 400

    nodes = pr["nodes"]
    key_to_graph = pr["key_to_graph"]
    graphs = pr["graphs"]
    type_filter = int(type_id) if type_id else None

    out = []
    for key, node in nodes.items():
        if node["table"] != table:
            continue
        gid = key_to_graph.get(key)
        if gid is None:
            continue
        g = graphs[str(gid)]
        if type_filter and g["type_id"] != type_filter:
            continue
        out.append({
            "pk": node["pk"],
            "label": node["label"],
            "graph_id": gid,
            "graph_size": g["size"],
            "type_id": g["type_id"],
        })
        if len(out) >= limit:
            break

    out.sort(key=lambda x: x["pk"])
    return jsonify({"status": "success", "table": table, "count": len(out), "ids": out})


def _bfs_component(pr, start_key, max_nodes):
    """BFS over the component containing start_key, capped at max_nodes.
    Returns (visited_keys, edges) where edges are within the visited set."""
    nodes = pr["nodes"]
    key_to_graph = pr["key_to_graph"]
    graph_members = pr["graphs"][str(key_to_graph[start_key])]["members"]

    # Build adjacency for this component (undirected).
    member_set = set(graph_members)
    adj = {}
    for k in member_set:
        for conn in nodes[k]["connections"]:
            t = conn["target_key"]
            if t in member_set:
                adj.setdefault(k, []).append((t, conn))
                adj.setdefault(t, []).append((k, conn))

    visited = set()
    order = []
    stack = [start_key]
    while stack and len(visited) < max_nodes:
        cur = stack.pop(0)
        if cur in visited:
            continue
        visited.add(cur)
        order.append(cur)
        for nb, _conn in adj.get(cur, []):
            if nb not in visited:
                stack.append(nb)

    # Collect edges within the visited set (dedup by unordered pair + field).
    edges = []
    seen = set()
    for k in visited:
        for conn in nodes[k]["connections"]:
            t = conn["target_key"]
            if t not in visited:
                continue
            pair = tuple(sorted([k, t])) + (conn["field"],)
            if pair in seen:
                continue
            seen.add(pair)
            edges.append({
                "source": k,
                "target": t,
                "field": conn["field"],
                "to_table": conn["to_table"],
            })
    return order, visited, edges


@graph_visualizer_bp.route('/graph_visualizer/graph/<dataset_id>', methods=['GET'])
def graph_route(dataset_id):
    """Return the component containing (table, id), with nodes + edges for rendering."""
    pr = _load_dataset(dataset_id)
    if not pr:
        return jsonify({"status": "error", "message": "Dataset not found"}), 404

    table = request.args.get("table")
    node_id = request.args.get("id")
    if not table or not node_id:
        return jsonify({"status": "error", "message": "table and id are required"}), 400

    start_key = f"{table}||{node_id}"
    nodes = pr["nodes"]
    if start_key not in nodes:
        return jsonify({"status": "error", "message": f"No row {table}/{node_id}"}), 404

    key_to_graph = pr["key_to_graph"]
    gid = key_to_graph.get(start_key)
    if gid is None:
        return jsonify({"status": "error", "message": "Row not assigned to a graph"}), 404

    g = pr["graphs"][str(gid)]
    max_nodes = min(int(request.args.get("max_nodes", 500)), 5000)

    order, visited, edges = _bfs_component(pr, start_key, max_nodes)

    out_nodes = []
    for k in order:
        node = nodes[k]
        out_nodes.append({
            "id": k,
            "table": node["table"],
            "pk": node["pk"],
            "label": node["label"],
            "fields": node["fields"],
            "is_focal": (k == start_key),
        })

    return jsonify({
        "status": "success",
        "dataset_id": dataset_id,
        "name": pr["name"],
        "table": table,
        "id": node_id,
        "graph_id": gid,
        "graph_size": g["size"],
        "type_id": g["type_id"],
        "rendered_count": len(out_nodes),
        "truncated": len(visited) < g["size"],
        "colors": pr["colors"],
        "hint_fields": pr["hint_fields"],
        "tables": g["tables"],
        "nodes": out_nodes,
        "edges": edges,
    })


@graph_visualizer_bp.route('/graph_visualizer/upload', methods=['POST'])
def upload_route():
    """Upload a zipped .sql file + a YAML schema file, process, and store."""
    sql_zip = request.files.get('sql_zip')
    if not sql_zip:
        return jsonify({"status": "error", "message": "sql_zip file is required"}), 400

    name = (request.form.get("name") or "").strip()

    try:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "upload.zip")
            sql_zip.save(zip_path)

            if not zipfile.is_zipfile(zip_path):
                return jsonify({"status": "error", "message": "Uploaded file is not a valid zip"}), 400

            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Prevent zip-slip.
                for member in zf.namelist():
                    dest = os.path.abspath(os.path.join(tmp, member))
                    if not dest.startswith(os.path.abspath(tmp) + os.sep):
                        return jsonify({"status": "error", "message": f"Unsafe zip entry: {member}"}), 400
                zf.extractall(tmp)

            # Locate the .sql file inside the zip.
            sql_path = None
            yaml_path = None
            for root, _dirs, files in os.walk(tmp):
                for fn in files:
                    full = os.path.join(root, fn)
                    low = fn.lower()
                    if low.endswith(".sql") and sql_path is None:
                        sql_path = full
                    elif (low.endswith(".yaml") or low.endswith(".yml")) and yaml_path is None:
                        yaml_path = full

            if not sql_path:
                return jsonify({"status": "error", "message": "No .sql file found in the zip"}), 400

            # YAML: prefer the separately uploaded file, else the one inside the zip.
            yaml_text = None
            yaml_file = request.files.get('yaml')
            if yaml_file and yaml_file.filename:
                yaml_text = yaml_file.read().decode("utf-8")
            elif yaml_path:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    yaml_text = f.read()

            if not yaml_text:
                return jsonify({"status": "error",
                                "message": "No YAML schema file provided (upload one or include it in the zip)"}), 400

            schema = _load_schema(yaml_text)
            if not name:
                name = schema["name"]

            with open(sql_path, "r", encoding="utf-8", errors="surrogateescape") as f:
                sql_text = f.read()

            nodes, row_counts = _parse_sql(sql_text, schema)
            key_to_graph, graph_members, type_of, types_list, edges_followed = _build_components(nodes, schema)

            colors = _assign_colors(schema["tables"])

            # Serialize pk for JSON (tuple -> list).
            json_tables = {}
            for tname, meta in schema["tables"].items():
                json_tables[tname] = {
                    "pk": meta["pk"] if isinstance(meta["pk"], str) else list(meta["pk"]),
                    "columns": meta["columns"],
                }

            # Per-graph summary (tables present + size + type).
            graphs_json = {}
            for gid, members in graph_members.items():
                tables_present = sorted({nodes[k]["table"] for k in members})
                graphs_json[str(gid)] = {
                    "size": len(members),
                    "type_id": type_of[gid],
                    "tables": tables_present,
                    "members": members,
                }

            dataset_id = uuid.uuid4().hex[:12]
            processed = {
                "dataset_id": dataset_id,
                "name": name,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "options": schema["options"],
                "tables": json_tables,
                "colors": colors,
                "hierarchy": schema["hierarchy"],
                "references": schema["references"],
                "hint_fields": schema["hint_fields"],
                "types": types_list,
                "graphs": graphs_json,
                "key_to_graph": key_to_graph,
                "nodes": nodes,
                "summary": {
                    "tables": len(json_tables),
                    "rows": len(nodes),
                    "rows_per_table": row_counts,
                    "graphs": len(graphs_json),
                    "types": len(types_list),
                    "edges_followed": edges_followed,
                    "largest_graph": max((g["size"] for g in graphs_json.values()), default=0),
                },
            }
            _save_dataset(dataset_id, processed)

            return jsonify({
                "status": "success",
                "dataset_id": dataset_id,
                "name": name,
                "summary": processed["summary"],
            })

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Processing failed: {e}"}), 500
