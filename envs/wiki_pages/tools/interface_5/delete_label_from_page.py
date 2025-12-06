import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteLabelFromPage(Tool):
    """Remove a label from a page."""

    @staticmethod
    def invoke(data: Dict[str, Any], page_id: str, page_label_id: str, deleted_by: str) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not page_id or not isinstance(page_id, str):
            return json.dumps({"success": False, "error": "page_id must be provided"})
        if not page_label_id or not isinstance(page_label_id, str):
            return json.dumps({"success": False, "error": "page_label_id must be provided"})
        if not deleted_by or not isinstance(deleted_by, str):
            return json.dumps({"success": False, "error": "deleted_by must be provided"})

        pages = data.get("pages", {})
        labels = data.get("page_labels", {})
        users = data.get("users", {})
        if not isinstance(pages, dict) or not isinstance(labels, dict) or not isinstance(users, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        if page_id not in pages:
            return json.dumps({"success": False, "error": f"Page '{page_id}' not found"})
        record = labels.get(page_label_id)
        if not record or record.get("page_id") != page_id:
            return json.dumps({"success": False, "error": "Label not associated with the page"})
        if deleted_by not in users:
            return json.dumps({"success": False, "error": f"User '{deleted_by}' not found"})

        removed = labels.pop(page_label_id)
        removed["deleted_by"] = deleted_by
        removed["deleted_at"] = "2025-12-02T12:00:00"
        return json.dumps({"success": True, "label": removed})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_label_from_page",
                "description": "Remove a label from a page.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Page identifier."},
                        "page_label_id": {"type": "string", "description": "Label identifier."},
                        "deleted_by": {"type": "string", "description": "User performing the deletion."},
                    },
                    "required": ["page_id", "page_label_id", "deleted_by"],
                },
            },
        }
