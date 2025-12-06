import json
from typing import Any, Dict, List
from tau_bench.envs.tool import Tool

class InsertDocPermission(Tool):
    """Add one or more doc-level permissions in Coda Workspace (Coda doc -> space in confluence)."""

    @staticmethod
    def invoke(data: Dict[str, Any], entries: List[Dict[str, Any]]) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(entries, list) or not entries:
            return json.dumps({"success": False, "error": "entries must be a non-empty list"})

        spaces = data.setdefault("spaces", {})
        users = data.setdefault("users", {})
        permissions = data.setdefault("permissions", {})
        if not all(isinstance(obj, dict) for obj in (spaces, users, permissions)):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        allowed_ops = {
            "view",
            "edit",
            "delete",
            "create",
            "admin",
            "restrict_other_users",
        }

        def next_permission_id() -> str:
            numeric_keys = []
            for perm_id in permissions.keys():
                try:
                    numeric_keys.append(int(perm_id))
                except (TypeError, ValueError):
                    continue
            return str(max(numeric_keys, default=0) + 1)

        created_records = []
        timestamp = "2025-12-02T12:00:00"

        for entry in entries:
            if not isinstance(entry, dict):
                return json.dumps({"success": False, "error": "Each entry must be an object"})

            doc_id = entry.get("doc_id")
            user_id = entry.get("user_id")
            operation = entry.get("operation")
            granted_by = entry.get("granted_by")

            if not all(isinstance(val, str) and val.strip() for val in (doc_id, user_id, operation, granted_by)):
                return json.dumps({"success": False, "error": "doc_id, user_id, operation, granted_by are required"})

            if doc_id not in spaces:
                return json.dumps({"success": False, "error": f"Doc '{doc_id}' not found"})
            if user_id not in users:
                return json.dumps({"success": False, "error": f"User '{user_id}' not found"})
            if granted_by not in users:
                return json.dumps({"success": False, "error": f"Granted_by user '{granted_by}' not found"})
            if operation not in allowed_ops:
                return json.dumps({"success": False, "error": f"Invalid operation '{operation}'"})

            for perm in permissions.values():
                if (
                    perm.get("content_id") == doc_id
                    and perm.get("content_type") == "space"
                    and perm.get("user_id") == user_id
                    and perm.get("operation") == operation
                ):
                    return json.dumps({"success": False, "error": "Permission already exists"})

            new_id = next_permission_id()
            record = {
                "permission_id": new_id,
                "content_id": doc_id,
                "content_type": "doc",
                "user_id": user_id,
                "operation": operation,
                "granted_by": granted_by,
                "granted_at": timestamp,
            }
            permissions[new_id] = record
            created_records.append(record)

        return json.dumps({"success": True, "count": len(created_records), "permissions": created_records})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "insert_doc_permission",
                "description": "Grant one or more permissions on a doc  by specifying doc, user, operation, and grantor.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entries": {
                            "type": "array",
                            "description": "List of permissions to create.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "doc_id": {"type": "string", "description": "Doc identifier."},
                                    "user_id": {"type": "string", "description": "User receiving the permission."},
                                    "operation": {
                                        "type": "string",
                                        "description": "Allowed values: view, edit, delete, create, admin, restrict_other_users.",
                                    },
                                    "granted_by": {
                                        "type": "string",
                                        "description": "User issuing the permission grant.",
                                    },
                                },
                                "required": ["doc_id", "user_id", "operation", "granted_by"],
                            },
                        }
                    },
                    "required": ["entries"],
                },
            },
        }
