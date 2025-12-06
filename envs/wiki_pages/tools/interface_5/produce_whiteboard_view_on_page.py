import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class ProduceWhiteboardViewOnPage(Tool):
    """Create a whiteboard hosted on a specific page."""

    @staticmethod
    def invoke(
        data: Dict[str, Any],
        title: str,
        host_page_id: str,
        host_doc_id: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(title, str) or not title.strip():
            return json.dumps({"success": False, "error": "title must be a non-empty string"})
        if not isinstance(host_page_id, str) or not host_page_id.strip():
            return json.dumps({"success": False, "error": "host_page_id must be provided"})

        whiteboards = data.setdefault("whiteboards", {})
        pages = data.setdefault("pages", {})
        spaces = data.setdefault("spaces", {})
        if not isinstance(whiteboards, dict) or not isinstance(pages, dict) or not isinstance(spaces, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        page = pages.get(host_page_id)
        if not page:
            return json.dumps({"success": False, "error": f"Host page '{host_page_id}' not found"})
        inferred_doc_id = page.get("space_id") or page.get("doc_id")
        if page.get("status") == "locked":
            return json.dumps({"success": False, "error": "Cannot create whiteboard on locked page"})
        if host_doc_id and host_doc_id != inferred_doc_id:
            return json.dumps({"success": False, "error": "Host doc does not match page's doc"})
        if inferred_doc_id and inferred_doc_id not in spaces:
            return json.dumps({"success": False, "error": "Host page references unknown doc"})

        desired_status = status or "current"
        allowed_status = {"current", "archived", "deleted", "locked"}
        if desired_status not in allowed_status:
            return json.dumps({"success": False, "error": "status must be current, archived, deleted, or locked"})

        def next_id(table: Dict[str, Any]) -> str:
            numeric = []
            for key in table.keys():
                try:
                    numeric.append(int(key))
                except (TypeError, ValueError):
                    continue
            return str(max(numeric, default=0) + 1)

        whiteboard_id = next_id(whiteboards)
        timestamp = "2025-12-02T12:00:00"
        record = {
            "whiteboard_id": whiteboard_id,
            "title": title.strip(),
            "host_page_id": host_page_id,
            "host_doc_id": inferred_doc_id,
            "content": content,
            "status": desired_status,
            "created_by": page.get("created_by"),
            "created_at": timestamp,
            "updated_by": page.get("created_by"),
            "updated_at": timestamp,
        }
        whiteboards[whiteboard_id] = record
        return json.dumps({"success": True, "whiteboard": record})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "produce_whiteboard_view_on_page",
                "description": "Create a whiteboard hosted on a page within a doc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Whiteboard title."},
                        "host_page_id": {"type": "string", "description": "Page hosting this whiteboard."},
                        "host_doc_id": {
                            "type": "string",
                            "description": "Optional doc ID (validated against page).",
                        },
                        "content": {"type": "string", "description": "Optional content payload."},
                        "status": {
                            "type": "string",
                            "description": "Status (current, archived, deleted, locked). Defaults to current.",
                        },
                    },
                    "required": ["title", "host_page_id"],
                },
            },
        }
