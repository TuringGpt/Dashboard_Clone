import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class DeleteWhiteboardViewWithContent(Tool):
    """Delete a whiteboard entry."""

    @staticmethod
    def invoke(
        data: Dict[str, Any],
        whiteboard_id: Optional[str] = None,
        deleted_by: Optional[str] = None,
    ) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not whiteboard_id or not isinstance(whiteboard_id, str):
            return json.dumps({"success": False, "error": "whiteboard_id must be provided"})
        if not deleted_by or not isinstance(deleted_by, str):
            return json.dumps({"success": False, "error": "deleted_by must be provided"})

        whiteboards = data.get("whiteboards", {})
        users = data.get("users", {})
        if not isinstance(whiteboards, dict) or not isinstance(users, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        record = whiteboards.get(whiteboard_id)
        if not record:
            return json.dumps({"success": False, "error": f"Whiteboard '{whiteboard_id}' not found"})
        if deleted_by not in users:
            return json.dumps({"success": False, "error": f"User '{deleted_by}' not found"})

        record["status"] = "deleted"
        record["deleted_by"] = deleted_by
        record["deleted_at"] = "2025-12-02T12:00:00"
        host_doc_id = record.pop("host_space_id", None)
        if host_doc_id:
            record["doc_id"] = host_doc_id
        return json.dumps({"success": True, "whiteboard": record})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_whiteboard_view_with_content",
                "description": "Delete a whiteboard record.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "whiteboard_id": {"type": "string", "description": "Whiteboard identifier."},
                        "deleted_by": {"type": "string", "description": "User performing the deletion."},
                    },
                    "required": ["whiteboard_id", "deleted_by"],
                },
            },
        }
