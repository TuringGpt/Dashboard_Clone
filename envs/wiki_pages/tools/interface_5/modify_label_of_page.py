import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class ModifyLabelOfPage(Tool):
    """Update label metadata for a page in Coda Workspace."""

    @staticmethod
    def invoke(
        data: Dict[str, Any],
        page_label_id: str,
        added_by: Optional[str] = None,
        label_name: Optional[str] = None,
    ) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(page_label_id, str) or not page_label_id.strip():
            return json.dumps({"success": False, "error": "page_label_id must be provided"})
        if label_name is None and added_by is None:
            return json.dumps({"success": False, "error": "At least one field must be updated"})

        labels = data.get("page_labels", {})
        users = data.get("users", {})
        if not isinstance(labels, dict) or not isinstance(users, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        record = labels.get(page_label_id)
        if not record:
            return json.dumps({"success": False, "error": f"Label '{page_label_id}' not found"})

        if added_by is not None:
            if not isinstance(added_by, str) or not added_by.strip():
                return json.dumps({"success": False, "error": "added_by must be a non-empty string"})
            if added_by not in users:
                return json.dumps({"success": False, "error": f"User '{added_by}' not found"})
            record["added_by"] = added_by

        if label_name is not None:
            if not isinstance(label_name, str) or not label_name.strip():
                return json.dumps({"success": False, "error": "label_name must be a non-empty string"})
            record["label_name"] = label_name

        record["updated_at"] = "2025-12-02T12:00:00"
        return json.dumps({"success": True, "label": record})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "modify_label_of_page",
                "description": "Update the label info attached to a page in Conda Workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_label_id": {"type": "string", "description": "Identifier of the label to update."},
                        "added_by": {"type": "string", "description": "New user who manages this label."},
                        "label_name": {"type": "string", "description": "New label text."},
                    },
                    "required": ["page_label_id"],
                },
            },
        }
