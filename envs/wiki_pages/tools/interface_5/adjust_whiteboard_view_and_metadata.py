import json
from typing import Any, Dict, List
from tau_bench.envs.tool import Tool

class AdjustWhiteboardViewAndMetadata(Tool):
    """Batch update whiteboard attributes (title/content/status)."""

    @staticmethod
    def invoke(data: Dict[str, Any], updates: List[Dict[str, Any]]) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(updates, list) or not updates:
            return json.dumps({"success": False, "error": "updates must be a non-empty list"})

        whiteboards = data.get("whiteboards", {})
        users = data.get("users", {})
        pages = data.get("pages", {})
        if not isinstance(whiteboards, dict) or not isinstance(users, dict) or not isinstance(pages, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        allowed_status = {"current", "archived", "deleted", "locked"}
        applied = []

        for entry in updates:
            if not isinstance(entry, dict):
                return json.dumps({"success": False, "error": "Each update entry must be an object"})

            wb_id = entry.get("whiteboard_view_id")
            updated_by = entry.get("updated_by")
            if not isinstance(wb_id, str) or not wb_id.strip():
                return json.dumps({"success": False, "error": "whiteboard_view_id is required"})
            if not isinstance(updated_by, str) or not updated_by.strip():
                return json.dumps({"success": False, "error": "updated_by is required"})

            record = whiteboards.get(wb_id)
            if not record:
                return json.dumps({"success": False, "error": f"Whiteboard '{wb_id}' not found"})
            if updated_by not in users:
                return json.dumps({"success": False, "error": f"User '{updated_by}' not found"})

            host_page_id = record.get("host_page_id")
            host_page = pages.get(host_page_id)
            if host_page and host_page.get("status") == "locked":
                return json.dumps({"success": False, "error": f"Host page '{host_page_id}' is locked"})

            status = entry.get("status")
            if record.get("status") == "locked" and status is None:
                return json.dumps({"success": False, "error": f"Whiteboard '{wb_id}' is locked"})

            changed = False
            title = entry.get("title")
            content = entry.get("content")

            if title is not None:
                if not isinstance(title, str) or not title.strip():
                    return json.dumps({"success": False, "error": "title must be a non-empty string"})
                record["title"] = title.strip()
                changed = True

            if content is not None:
                if content and not isinstance(content, str):
                    return json.dumps({"success": False, "error": "content must be string or null"})
                record["content"] = content
                changed = True

            if status is not None:
                if status not in allowed_status:
                    return json.dumps({"success": False, "error": "Invalid whiteboard status"})
                record["status"] = status
                changed = True

            if not changed:
                return json.dumps({"success": False, "error": "No changes supplied for whiteboard"})

            record["updated_by"] = updated_by
            record["updated_at"] = "2025-12-02T12:00:00"
            applied.append({"whiteboard_view_id": wb_id, "status": record["status"]})

        return json.dumps({"success": True, "updated": applied, "count": len(applied)})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "adjust_whiteboard_view_and_metadata",
                "description": "Batch update whiteboard titles, content, or status.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "updates": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "whiteboard_view_id": {"type": "string", "description": "Whiteboard identifier."},
                                    "title": {"type": "string", "description": "Optional new title."},
                                    "content": {"type": "string", "description": "Optional content payload."},
                                    "status": {
                                        "type": "string",
                                        "description": "Optional status (current, archived, deleted, locked).",
                                    },
                                    "updated_by": {"type": "string", "description": "User applying the update."},
                                },
                                "required": ["whiteboard_view_id", "updated_by"],
                            },
                        }
                    },
                    "required": ["updates"],
                },
            },
        }
