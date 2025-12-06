import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

STATUS_VALUES = {"current", "archived", "deleted"}

class ModifyTableData(Tool):
    """Update table (database in confluence) metadata such as title, description, or status."""

    @staticmethod
    def invoke(
        data: Dict[str, Any],
        table_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(table_id, str) or not table_id.strip():
            return json.dumps({"success": False, "error": "table_id must be provided"})
        if updated_by is None or not isinstance(updated_by, str) or not updated_by.strip():
            return json.dumps({"success": False, "error": "updated_by must be provided"})
        if title is None and description is None and status is None:
            return json.dumps({"success": False, "error": "No changes supplied"})

        databases = data.get("databases", {})
        users = data.get("users", {})
        if not isinstance(databases, dict) or not isinstance(users, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        record = databases.get(table_id)
        if not record:
            return json.dumps({"success": False, "error": f"Table '{table_id}' not found"})
        if updated_by not in users:
            return json.dumps({"success": False, "error": f"User '{updated_by}' not found"})

        if title is not None:
            if not isinstance(title, str) or not title.strip():
                return json.dumps({"success": False, "error": "title must be a non-empty string"})
            record["title"] = title.strip()
        if description is not None:
            if description and not isinstance(description, str):
                return json.dumps({"success": False, "error": "description must be a string"})
            record["description"] = description
        if status is not None:
            if status not in STATUS_VALUES:
                return json.dumps({"success": False, "error": "status must be current, archived, or deleted"})
            record["status"] = status

        record["updated_by"] = updated_by
        record["updated_at"] = "2025-12-02T12:00:00"

        response_record = dict(record)
        response_record["table_id"] = response_record.pop("database_id")
        host_doc_id = response_record.pop("host_space_id", None)
        if host_doc_id:
            response_record["doc_id"] = host_doc_id
        return json.dumps({"success": True, "table": response_record})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "modify_table_data",
                "description": "Update table metadata (title, description, status) in Coda.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_id": {"type": "string", "description": "Identifier of the table to update."},
                        "title": {"type": "string", "description": "New table title (optional)."},
                        "description": {"type": "string", "description": "New table description (optional)."},
                        "status": {
                            "type": "string",
                            "description": "Lifecycle status (current, archived, deleted).",
                        },
                        "updated_by": {"type": "string", "description": "User performing the update."},
                    },
                    "required": ["table_id", "updated_by"],
                },
            },
        }
