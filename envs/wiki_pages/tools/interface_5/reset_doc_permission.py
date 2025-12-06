import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class ResetDocPermission(Tool):
    """Remove an existing doc  permission entry identified by permission_id and operation."""

    @staticmethod
    def invoke(data: Dict[str, Any], operation: str, permission_id: str) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(permission_id, str) or not permission_id.strip():
            return json.dumps({"success": False, "error": "permission_id must be a non-empty string"})
        if not isinstance(operation, str) or not operation.strip():
            return json.dumps({"success": False, "error": "operation must be a non-empty string"})

        permissions = data.get("permissions", {})
        if not isinstance(permissions, dict):
            return json.dumps({"success": False, "error": "Corrupted permissions store"})

        record = permissions.get(permission_id)
        if not record:
            return json.dumps({"success": False, "error": f"Permission '{permission_id}' not found"})
        if record.get("operation") != operation:
            return json.dumps({"success": False, "error": "Operation mismatch for permission"})

        removed = permissions.pop(permission_id)
        return json.dumps({"success": True, "permission_id": permission_id, "removed": removed})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "reset_doc_permission",
                "description": "Remove a specific permission from a doc by permission_id and expected operation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "permission_id": {"type": "string", "description": "Identifier of the permission to remove."},
                        "operation": {
                            "type": "string",
                            "description": "Operation value to confirm before deletion (view/edit/delete/create/admin/restrict_other_users).",
                        },
                    },
                    "required": ["permission_id", "operation"],
                },
            },
        }
