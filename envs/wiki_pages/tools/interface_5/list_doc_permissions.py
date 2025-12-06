import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class ListDocPermissions(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], doc_id: str) -> str:
        """List every permission entry tied to the specified doc."""
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})

        spaces = data.get("spaces", {})
        permissions = data.get("permissions", {})
        users = data.get("users", {})
        if not all(isinstance(obj, dict) for obj in (spaces, permissions, users)):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        if doc_id not in spaces:
            return json.dumps({"success": False, "error": f"Doc with ID '{doc_id}' not found"})

        doc_permissions = []
        for perm_id, perm_data in permissions.items():
            if perm_data.get("content_id") == doc_id and perm_data.get("content_type") in {"space"}:
                doc_permissions.append(
                    {
                        "permission_id": perm_id,
                        "operation": perm_data.get("operation"),
                        "granted_by": perm_data.get("granted_by"),
                        "granted_at": perm_data.get("granted_at"),
                    }
                )

        return json.dumps(
            {
                "success": True,
                "doc_id": doc_id,
                "permissions": doc_permissions,
                "count": len(doc_permissions),
            }
        )

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_doc_permissions",
                "description": "List every permission record associated with a doc as permissions are doc level in Coda Workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "Unique identifier of the doc"
                        }
                    },
                    "required": ["doc_id"]
                }
            }
        }
