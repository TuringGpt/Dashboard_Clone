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
import random
import zipfile
import tempfile
import shutil
from datetime import datetime

import yaml
from flask import Blueprint, render_template, request, jsonify, abort

graph_visualizer_bp = Blueprint('graph_visualizer', __name__)

# Store processed datasets OUTSIDE the application source tree. Writing a multi-MB
# file inside the tree (e.g. under modules/) triggers the Werkzeug debug reloader
# to restart the worker mid-request, which resets the in-flight upload connection
# and surfaces in the browser as "Failed to fetch". Override with the
# GRAPH_VISUALIZER_DATA_DIR env var; defaults to a dir in the system temp location.
DATA_DIR = os.environ.get(
    "GRAPH_VISUALIZER_DATA_DIR",
    os.path.join(tempfile.gettempdir(), "graph_visualizer_data"),
)
os.makedirs(DATA_DIR, exist_ok=True)

# In-memory cache of processed datasets, keyed by dataset_id.
_DATASETS = {}
# Per-dataset table index: {dataset_id: {table_name: [node_keys]}}.
# Built lazily on first /ids request so subsequent lookups are O(1) per table
# instead of scanning all nodes.
_TABLE_INDEX = {}

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


def _normalize_email_join(ej):
    """Normalize the email_join config to a dict or None.

    Supports two YAML forms:
      1. dict (preferred, fully generic):
           email_join:
             column: organizer_email
             target_table: users
             target_column: email
      2. string (legacy shorthand, targets users.email implicitly):
           email_join: organizer_email
    Returns None if no email_join is configured.
    """
    if not ej:
        return None
    if isinstance(ej, str):
        return {"column": ej, "target_table": "users", "target_column": "email"}
    return {
        "column": ej["column"],
        "target_table": ej.get("target_table", "users"),
        "target_column": ej.get("target_column", "email"),
    }


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
            "email_join": _normalize_email_join(meta.get("email_join")),
        }

    options = data.get("options", {}) or {}
    schema = {
        "name": data.get("name", "dataset"),
        "description": data.get("description", ""),
        "version": data.get("version", 1),
        "options": {
            "max_field_len": int(options.get("max_field_len", 120)),
            "exclude_hubs": list(options.get("exclude_hubs", []) or []),
            "noise_fields": list(options.get("noise_fields", []) or []),
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
    """Truncate a value for display. Returns (truncated_str, full_str_or_None).

    full_str is None when no truncation was needed, otherwise the original
    untruncated value (so the client can show it in a popup on click).
    """
    if v is None:
        return "", None
    s = str(v)
    if len(s) > max_len:
        return s[:max_len] + f"...(+{len(s) - max_len} chars)", s
    return s, None


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

def _parse_sql(sql_text, schema, from_path=False):
    """Parse the seed SQL using the YAML schema. Returns (nodes, row_counts).

    Single pass: builds nodes, collects real_id_sets, and defers conditional
    edges + value-join edges until the end (when all real_id_sets are known).
    This is 2x faster than the old 2-pass approach for large files.

    By default sql_text is the full SQL string. Pass from_path=True and a file
    path in sql_text to stream line-by-line instead — this avoids loading the
    entire SQL file (which can be >1GB) into memory at once.
    """
    max_len = schema["options"]["max_field_len"]
    tables = schema["tables"]
    hint_fields = schema["hint_fields"]
    nodes = {}
    row_counts = {t: 0 for t in tables}

    # Sets to resolve conditional edges (only follow when target is a real row).
    real_id_sets = {t: set() for t in tables}      # table -> {pk_value}

    # Value-join maps: for each (target_table, target_column) that some table's
    # email_join points at, map the target_column value -> pk_display of that row.
    value_join_targets = set()   # {(target_table, target_column)}
    for meta in tables.values():
        ej = meta.get("email_join")
        if ej:
            value_join_targets.add((ej["target_table"], ej["target_column"]))
    value_join_maps = {}  # {(target_table, target_column): {value: pk_display}}

    # Deferred edges: (node_key, edge_spec, fk_value) — resolved after pass 1
    # completes, when all real_id_sets + value_join_maps are fully built.
    deferred_conditional = []   # (node_key, edge_dict, fk_value)
    deferred_value_joins = []   # (node_key, ej_config, join_value)

    if from_path:
        # Stream line-by-line to avoid loading the entire SQL file into memory.
        # (A 1GB+ dump read via .read()+splitlines() doubles memory and OOMs.)
        def _line_iter():
            with open(sql_text, "r", encoding="utf-8", errors="surrogateescape") as f:
                for raw in f:
                    yield raw.rstrip("\r\n")
        it = _line_iter()
    else:
        it = iter(sql_text.splitlines(keepends=False))

    cur_table = None
    col_names = []
    col_index = {}
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

        meta = tables[cur_table]
        pk = meta["pk"]

        # --- compute pk_display + populate real_id_sets ---
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

        real_id_sets[cur_table].add(pk_display)

        # --- populate value-join maps (if this table is a join target) ---
        for (jt_table, jt_col) in value_join_targets:
            if cur_table == jt_table and jt_col in col_index:
                jv = vals[col_index[jt_col]]
                if jv is not None and jv != "":
                    key_pair = (jt_table, jt_col)
                    value_join_maps.setdefault(key_pair, {})[jv] = pk_display

        key = f"{cur_table}||{pk_display}"

        # --- build truncated field dict ---
        declared = meta["columns"] or col_names
        fields = {}
        full_fields = {}
        for c in declared:
            if c in col_index and col_index[c] < len(vals):
                t, full = _truncate(vals[col_index[c]], max_len)
                fields[c] = t
                if full is not None:
                    full_fields[c] = full

        # --- label ---
        hf = hint_fields.get(cur_table)
        label = fields.get(hf) if hf else None
        if not label:
            label = pk_display
        if len(str(label)) > 60:
            label = str(label)[:60] + "..."

        # --- connections: non-conditional edges now, conditional deferred ---
        connections = []
        for e in meta["edges"]:
            if e["column"] not in col_index:
                continue
            fv = vals[col_index[e["column"]]]
            if fv is None or fv == "":
                continue
            if e["conditional"]:
                # Defer — we don't know yet if the target exists.
                deferred_conditional.append((key, e, fv))
                continue
            tgt_table = e["to_table"]
            tgt_key = f"{tgt_table}||{fv}"
            connections.append({
                "field": e["column"],
                "to_table": tgt_table,
                "to_pk": fv,
                "target_key": tgt_key,
                "conditional": False,
            })

        # --- value-join (email_join): defer (target map may not be built yet) ---
        ej = meta.get("email_join")
        if ej and ej["column"] in col_index:
            jv = vals[col_index[ej["column"]]]
            if jv and jv != "":
                deferred_value_joins.append((key, ej, jv))

        nodes[key] = {
            "table": cur_table,
            "pk": pk_display,
            "label": label,
            "fields": fields,
            "full_fields": full_fields,
            "connections": connections,
        }
        row_counts[cur_table] += 1

    # --- resolve deferred conditional edges ---
    for key, e, fv in deferred_conditional:
        tgt_table = e["to_table"]
        if tgt_table not in real_id_sets or fv not in real_id_sets[tgt_table]:
            continue
        nodes[key]["connections"].append({
            "field": e["column"],
            "to_table": tgt_table,
            "to_pk": fv,
            "target_key": f"{tgt_table}||{fv}",
            "conditional": True,
        })

    # --- resolve deferred value-join (email_join) edges ---
    for key, ej, jv in deferred_value_joins:
        key_pair = (ej["target_table"], ej["target_column"])
        vmap = value_join_maps.get(key_pair, {})
        if jv in vmap:
            tgt_pk = vmap[jv]
            nodes[key]["connections"].append({
                "field": ej["column"],
                "to_table": ej["target_table"],
                "to_pk": tgt_pk,
                "target_key": f"{ej['target_table']}||{tgt_pk}",
                "conditional": True,
            })

    return nodes, row_counts


# ---------------------------------------------------------------------------
# Connected components (union-find) + graph typing
# ---------------------------------------------------------------------------

def _build_components(nodes, schema):
    """Assign each real node to a connected component. Returns:
       key_to_graph, graph_members, graph_flows, flows_list
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
    flow_of = {}
    flows_list = []
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
        # Flow signature: tables present + root tables only (NOT edge types).
        # Including edge types caused visually-identical groups to split into
        # separate flows (e.g. "pages with parent" vs "pages without parent"
        # both look like just "pages" to the user).
        sig = (tuple(tables_present), tuple(root_tables))
        if sig not in sig_index:
            tid = len(flows_list) + 1
            sig_index[sig] = tid
            flows_list.append({
                "flow_id": tid,
                "tables": list(tables_present),
                "root_tables": list(root_tables),
                "edges": [list(e) for e in sorted(edge_types)],
                "count": 0,
                "graph_ids": [],
            })
        tid = sig_index[sig]
        flow_of[gid] = tid
        t = flows_list[tid - 1]
        t["count"] += 1
        t["graph_ids"].append(gid)

    return key_to_graph, graph_members, flow_of, flows_list, edges_followed


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
    # Lightweight metadata for fast dataset listing — avoids loading the
    # full processed.json (which can be 500MB+) just to show the cards.
    meta = {
        "id": dataset_id,
        "name": processed.get("name", dataset_id),
        "created_at": processed.get("created_at"),
        "summary": processed.get("summary", {}),
    }
    with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    _DATASETS[dataset_id] = processed
    # Pre-build the per-table index so the first /ids request is instant.
    idx = {}
    for key, node in processed["nodes"].items():
        idx.setdefault(node["table"], []).append(key)
    _TABLE_INDEX[dataset_id] = idx


def _load_meta(dataset_id):
    """Load only the lightweight metadata for a dataset (name + summary)."""
    path = os.path.join(_dataset_dir(dataset_id), "meta.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


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


def _get_table_index(dataset_id):
    """Build (if needed) and return the per-table node index for a dataset.
    Maps table_name -> list of node keys, so /ids doesn't scan all nodes.
    """
    if dataset_id in _TABLE_INDEX:
        return _TABLE_INDEX[dataset_id]
    pr = _load_dataset(dataset_id)
    if not pr:
        return {}
    idx = {}
    for key, node in pr["nodes"].items():
        idx.setdefault(node["table"], []).append(key)
    _TABLE_INDEX[dataset_id] = idx
    return idx


def _list_datasets():
    out = []
    if not os.path.isdir(DATA_DIR):
        return out
    for name in sorted(os.listdir(DATA_DIR)):
        p = os.path.join(DATA_DIR, name, "processed.json")
        if not os.path.exists(p):
            continue
        # Fast path: read the lightweight meta.json (~200 bytes) instead of
        # loading the full processed.json (can be 500MB+).
        meta = _load_meta(name)
        if meta:
            out.append(meta)
        else:
            # Fallback: full load (old datasets without meta.json).
            pr = _load_dataset(name)
            if pr:
                out.append({
                    "id": name,
                    "name": pr.get("name", name),
                    "created_at": pr.get("created_at"),
                    "summary": pr.get("summary", {}),
                })
    return out


def _delete_dataset(dataset_id):
    """Remove a dataset from the in-memory cache and from disk.

    Returns True if anything was removed, False if the dataset was not found.
    Validates dataset_id (hex chars only) to prevent path traversal.
    """
    if not re.fullmatch(r"[0-9a-fA-F]{1,64}", dataset_id or ""):
        raise ValueError("Invalid dataset id")

    removed = False
    if dataset_id in _DATASETS:
        del _DATASETS[dataset_id]
        removed = True
    if dataset_id in _TABLE_INDEX:
        del _TABLE_INDEX[dataset_id]

    d = _dataset_dir(dataset_id)
    # Ensure we only remove a directory that actually lives under DATA_DIR.
    if os.path.abspath(d) != os.path.join(
            os.path.abspath(DATA_DIR), dataset_id):
        raise ValueError("Invalid dataset path")
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)
        removed = True
    return removed


# ---------------------------------------------------------------------------
# Blueprint routes
# ---------------------------------------------------------------------------

@graph_visualizer_bp.route('/graph_visualizer', strict_slashes=False, methods=['GET'])
def graph_visualizer():
    return render_template('graph_visualizer.html')


@graph_visualizer_bp.route('/graph_visualizer/yaml_prompt', methods=['GET'])
def yaml_prompt_route():
    """Return the YAML schema generation prompt text for the popup copy button."""
    prompt_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                              "prompts", "graph_visualizer")
    candidates = [
        os.path.join(prompt_dir, "yaml_generation_prompt.txt"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return jsonify({"status": "success", "prompt": f.read()})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "error", "message": "YAML prompt file not found"}), 404


@graph_visualizer_bp.route('/graph_visualizer/datasets', methods=['GET'])
def datasets_route():
    return jsonify({"status": "success", "datasets": _list_datasets()})


@graph_visualizer_bp.route('/graph_visualizer/delete/<dataset_id>', methods=['POST'])
def delete_route(dataset_id):
    try:
        removed = _delete_dataset(dataset_id)
        if not removed:
            return jsonify({"status": "error", "message": "Dataset not found"}), 404
        return jsonify({
            "status": "success",
            "message": f"Dataset '{dataset_id}' deleted",
            "dataset_id": dataset_id,
        })
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Delete failed: {e}"}), 500


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
        "flows": pr["flows"],
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
            "flow_id": meta["flow_id"],
            "tables": meta["tables"],
        })
    return jsonify({"status": "success", "graphs": graphs})


@graph_visualizer_bp.route('/graph_visualizer/ids/<dataset_id>', methods=['GET'])
def ids_route(dataset_id):
    """List ids for a table (for the id dropdown). Optionally filter by graph type.

    Query params:
      flow    - optional, filter by graph flow id
      sample  - optional, return N random ids per table instead of all (default: 10)
      limit   - optional, hard cap per table (default 2000, max 5000)
      table   - table name, or "__all__" / empty to return ids from ALL tables
    """
    pr = _load_dataset(dataset_id)
    if not pr:
        return jsonify({"status": "error", "message": "Dataset not found"}), 404
    table = request.args.get("table") or ""
    flow_id = request.args.get("flow") or request.args.get("type")
    sample_n = int(request.args.get("sample", 0))
    limit = min(int(request.args.get("limit", 2000)), 5000)

    all_tables = (table == "" or table == "__all__")

    if not all_tables and table not in pr["tables"]:
        return jsonify({"status": "error", "message": f"Unknown table: {table}"}), 400

    nodes = pr["nodes"]
    key_to_graph = pr["key_to_graph"]
    graphs = pr["graphs"]
    flow_filter = int(flow_id) if flow_id else None

    # Use the per-table index for O(1) lookup instead of scanning all nodes.
    table_index = _get_table_index(dataset_id)

    # When all_tables, collect ids per table so we can sample per table.
    if all_tables:
        target_tables = sorted(pr["tables"].keys())
    else:
        target_tables = [table]

    out = []
    for tbl in target_tables:
        table_ids = []
        for key in table_index.get(tbl, []):
            gid = key_to_graph.get(key)
            if gid is None:
                continue
            g = graphs[str(gid)]
            if flow_filter and g["flow_id"] != flow_filter:
                continue
            node = nodes[key]
            table_ids.append({
                "pk": node["pk"],
                "label": node["label"],
                "table": tbl,
                "graph_id": gid,
                "graph_size": g["size"],
                "flow_id": g["flow_id"],
            })
        # Sample per table when all_tables, or for the single table.
        if sample_n > 0 and len(table_ids) > sample_n:
            table_ids = random.sample(table_ids, sample_n)
        elif limit and len(table_ids) > limit:
            table_ids = table_ids[:limit]
        out.extend(table_ids)

    total = len(out)
    out.sort(key=lambda x: (x.get("table", ""), x["pk"]))
    return jsonify({
        "status": "success",
        "table": table,
        "count": len(out),
        "total": total,
        "ids": out,
    })


@graph_visualizer_bp.route('/graph_visualizer/flow_sample/<dataset_id>', methods=['GET'])
def flow_sample_route(dataset_id):
    """Return a representative graph from a given flow (when no specific id is picked).

    Picks the first member node of the first graph in the flow and returns the
    full graph for that node — same shape as /graph.
    """
    pr = _load_dataset(dataset_id)
    if not pr:
        return jsonify({"status": "error", "message": "Dataset not found"}), 404

    flow_id = request.args.get("flow")
    if not flow_id:
        return jsonify({"status": "error", "message": "flow is required"}), 400

    try:
        flow_id = int(flow_id)
    except ValueError:
        return jsonify({"status": "error", "message": "flow must be a number"}), 400

    flows = pr.get("flows", [])
    flow = next((f for f in flows if f["flow_id"] == flow_id), None)
    if not flow:
        return jsonify({"status": "error", "message": f"Flow {flow_id} not found"}), 404

    graph_ids = flow.get("graph_ids", [])
    if not graph_ids:
        return jsonify({"status": "error", "message": "No graphs in this flow"}), 404

    # Pick the first graph, then its first member node as the focal point.
    gid = graph_ids[0]
    members = pr["graphs"].get(str(gid), {}).get("members", [])
    if not members:
        return jsonify({"status": "error", "message": "Graph has no members"}), 404

    start_key = members[0]
    nodes = pr["nodes"]
    if start_key not in nodes:
        return jsonify({"status": "error", "message": "Member node not found"}), 404

    table, node_id = start_key.split("||", 1)
    max_nodes = min(int(request.args.get("max_nodes", 500)), 5000)
    lock = request.args.get("lock", "0") in ("1", "true", "True")

    if lock:
        order, visited, edges = _lock_component(pr, start_key)
    else:
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
            "full_fields": node.get("full_fields", {}),
            "is_focal": (k == start_key),
        })

    g = pr["graphs"][str(gid)]
    return jsonify({
        "status": "success",
        "dataset_id": dataset_id,
        "name": pr["name"],
        "table": table,
        "id": node_id,
        "graph_id": gid,
        "graph_size": g["size"],
        "flow_id": g["flow_id"],
        "rendered_count": len(out_nodes),
        "truncated": len(order) < g["size"],
        "locked": lock,
        "colors": pr["colors"],
        "hint_fields": pr["hint_fields"],
        "tables": g["tables"],
        "nodes": out_nodes,
        "edges": edges,
    })


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


def _lock_component(pr, start_key):
    """Return ONLY the focal node + its direct 1-hop neighbors (lock mode).

    Only includes neighbors that are in the SAME connected component (i.e.
    edges that were NOT dropped by exclude_hubs). This ensures lock mode
    shows the same set of nodes that would appear in the full BFS view.

    Same return signature as _bfs_component: (order, visited_set, edges).
    """
    nodes = pr["nodes"]
    key_to_graph = pr["key_to_graph"]
    gid = key_to_graph.get(start_key)
    if gid is None:
        return [start_key], {start_key}, []
    # The component's members — only these nodes are reachable.
    member_set = set(pr["graphs"][str(gid)]["members"])
    visited = {start_key}
    order = [start_key]

    # Add direct neighbors that are in the same component (outgoing).
    for conn in nodes[start_key]["connections"]:
        tk = conn["target_key"]
        if tk in member_set and tk not in visited:
            visited.add(tk)
            order.append(tk)
    # Incoming: any node in the same component whose connection target == start_key.
    for k in member_set:
        if k == start_key or k in visited:
            continue
        for conn in nodes[k]["connections"]:
            if conn["target_key"] == start_key:
                visited.add(k)
                order.append(k)
                break

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
    lock = request.args.get("lock", "0") in ("1", "true", "True")

    if lock:
        # Lock mode: return ONLY the focal node + its direct 1-hop neighbors.
        order, visited, edges = _lock_component(pr, start_key)
    else:
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
            "full_fields": node.get("full_fields", {}),
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
        "flow_id": g["flow_id"],
        "rendered_count": len(out_nodes),
        "truncated": len(visited) < g["size"],
        "locked": lock,
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

            # Parse the YAML schema (fast). The SQL file is streamed line-by-line
            # inside _parse_sql — this avoids reading a multi-GB dump into memory
            # (which OOM-kills the process).
            schema = _load_schema(yaml_text)

            if not name:
                name = schema["name"]

            nodes, row_counts = _parse_sql(sql_path, schema, from_path=True)
            key_to_graph, graph_members, flow_of, flows_list, edges_followed = _build_components(nodes, schema)

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
                    "flow_id": flow_of[gid],
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
                "flows": flows_list,
                "graphs": graphs_json,
                "key_to_graph": key_to_graph,
                "nodes": nodes,
                "summary": {
                    "tables": len(json_tables),
                    "rows": len(nodes),
                    "rows_per_table": row_counts,
                    "graphs": len(graphs_json),
                    "flows": len(flows_list),
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
