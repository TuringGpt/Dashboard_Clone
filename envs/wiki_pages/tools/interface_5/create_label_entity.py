import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class CreateLabelEntity(Tool):
    """Assign a label to a page."""

    @staticmethod
    def invoke(data: Dict[str, Any], fields: Dict[str, Any]) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(fields, dict):
            return json.dumps({"success": False, "error": "fields must be an object"})

        def next_label_id(table: Dict[str, Any]) -> str:
            numeric = []
            for key in table.keys():
                try:
                    numeric.append(int(key))
                except (TypeError, ValueError):
                    continue
            return str(max(numeric, default=0) + 1)

        page_id = fields.get("page_id")
        label_name = fields.get("label_name")
        added_by = fields.get("added_by")

        if not all(isinstance(val, str) and val.strip() for val in (page_id, label_name, added_by)):
            return json.dumps({"success": False, "error": "page_id, label_name, added_by are required"})

        pages = data.get("pages", {})
        users = data.get("users", {})
        labels = data.setdefault("page_labels", {})
        if not isinstance(pages, dict) or not isinstance(users, dict) or not isinstance(labels, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        if page_id not in pages:
            return json.dumps({"success": False, "error": f"Page '{page_id}' not found"})
        if added_by not in users:
            return json.dumps({"success": False, "error": f"User '{added_by}' not found"})

        for label in labels.values():
            if label.get("page_id") == page_id and label.get("label_name") == label_name:
                return json.dumps({"success": False, "error": "Label already applied"})

        label_id = next_label_id(labels)
        timestamp = "2025-12-02T12:00:00"
        record = {
            "page_label_id": label_id,
            "page_id": page_id,
            "label_name": label_name,
            "added_by": added_by,
            "added_at": timestamp,
        }
        labels[label_id] = record

        return json.dumps({"success": True, "label": record})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_label_entity",
                "description": "Assign a label to a page.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "properties": {
                                "page_id": {"type": "string", "description": "Page identifier."},
                                "label_name": {"type": "string", "description": "Label to apply."},
                                "added_by": {"type": "string", "description": "User assigning the label."},
                            },
                            "required": ["page_id", "label_name", "added_by"],
                        }
                    },
                    "required": ["fields"],
                },
            },
        }
