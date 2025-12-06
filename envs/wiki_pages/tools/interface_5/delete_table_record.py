import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteTableRecord(Tool):
    """Delete a table (database in confluence) record."""

    @staticmethod
    def invoke(data: Dict[str, Any], table_id: str, deleted_by: str) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(table_id, str) or not table_id.strip():
            return json.dumps({"success": False, "error": "table_id must be provided"})
        if not isinstance(deleted_by, str) or not deleted_by.strip():
            return json.dumps({"success": False, "error": "deleted_by must be provided"})

        databases = data.get("databases", {})
        users = data.get("users", {})
        if not isinstance(databases, dict) or not isinstance(users, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        if deleted_by not in users:
            return json.dumps({"success": False, "error": f"User '{deleted_by}' not found"})

        record = databases.get(table_id)
        if not record:
            return json.dumps({"success": False, "error": f"Table '{table_id}' not found"})

        removed = databases.pop(table_id)
        removed["deleted_by"] = deleted_by
        removed["deleted_at"] = "2025-12-02T12:00:00"
        response = dict(removed)
        response["table_id"] = response.pop("database_id", table_id)
        host_doc_id = response.pop("host_space_id", None)
        if host_doc_id:
            response["doc_id"] = host_doc_id
        return json.dumps({"success": True, "table": response})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_table_record",
                "description": "Delete a table by id.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_id": {"type": "string", "description": "Identifier of the table to remove."},
                        "deleted_by": {"type": "string", "description": "User performing the deletion."},
                    },
                    "required": ["table_id", "deleted_by"],
                },
            },
        }
