import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class EliminatePageFromWorkspace(Tool):
    """Delete or soft-delete a page. Permanent delete removes it entirely; otherwise mark status deleted."""

    @staticmethod
    def invoke(data: Dict[str, Any], page_id: str, permanent_delete: Optional[str] = None) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(page_id, str) or not page_id.strip():
            return json.dumps({"success": False, "error": "page_id must be provided"})

        pages = data.get("pages", {})
        if not isinstance(pages, dict):
            return json.dumps({"success": False, "error": "Corrupted pages store"})

        page = pages.get(page_id)
        if not page:
            return json.dumps({"success": False, "error": f"Page '{page_id}' not found"})

        timestamp = "2025-12-02T12:00:00"
        def to_bool(value: Optional[str]) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in {"true", "1", "yes"}
            return False

        permanent = to_bool(permanent_delete)

        if permanent:
            if page.get("status") == "locked":
                return json.dumps({"success": False, "error": "Locked page cannot be permanently deleted"})
            removed_page = pages.pop(page_id)
            removed_page["deleted_at"] = timestamp
            removed_page["permanent"] = True
            space_id = removed_page.pop("space_id", None)
            if space_id:
                removed_page["doc_id"] = space_id
            return json.dumps({"success": True, "page": removed_page})

        if page.get("status") == "locked":
            return json.dumps({"success": False, "error": "Locked page cannot be deleted"})
        page["status"] = "deleted"
        page["updated_at"] = timestamp
        page["permanent"] = False
        space_id = page.pop("space_id", None)
        if space_id:
            page["doc_id"] = space_id
        return json.dumps({"success": True, "page": page})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "eliminate_page_from_workspace",
                "description": "Delete a page. 'permanent_delete' removes it entirely; otherwise mark status deleted.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Identifier of the page to delete."},
                        "permanent_delete": {
                            "type": "string",
                            "description": "Treat as truthy ('true', '1', 'yes') to remove permanently. Defaults to false.",
                        },
                    },
                    "required": ["page_id"],
                },
            },
        }
