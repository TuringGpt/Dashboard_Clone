import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class ModifyAccessPermission(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        permission_id: str,
        operation: Optional[str] = None,
        user_id: Optional[str] = None,
        granted_by: Optional[str] = None,
    ) -> str:
        """
        Updates an existing permission record to change access levels or permissions holder.
        
        Allows modification of: operation (permission type), user (permission recipient), 
        or granter (who delegated the permission).
        
        Note: You can only modify direct permissions explicitly granted on a page; 
        inherited permissions from parent documents or containing workspace cannot be modified here.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not permission_id:
            return json.dumps({"error": "Missing required parameter: permission_id is required"})

        permission_id = str(permission_id)

        # Map Confluence DB terminology back to Fibery for output
        confluence_to_fibery_content_type = {
            "space": "workspace",
            "page": "document",
        }

        permissions = data.get("permissions", {})
        if permission_id not in permissions:
            return json.dumps({"error": f"Permission with ID '{permission_id}' not found"})

        permission = permissions[permission_id]

        # Validate operation if provided
        if operation is not None:
            allowed_operations = ["view", "edit", "delete", "create", "admin", "restrict_other_users"]
            if operation not in allowed_operations:
                return json.dumps({
                    "error": f"Invalid operation. Allowed values: {', '.join(allowed_operations)}"
                })

        # Validate user_id if provided
        if user_id is not None:
            user_id = str(user_id)
            users = data.get("users", {})
            if user_id not in users:
                return json.dumps({"error": f"User with ID '{user_id}' not found"})

        # Validate granted_by if provided
        if granted_by is not None:
            granted_by = str(granted_by)
            users = data.get("users", {})
            if granted_by not in users:
                return json.dumps({"error": f"Granting user with ID '{granted_by}' not found"})

        # Update fields if provided
        if operation is not None:
            permission["operation"] = operation
        if user_id is not None:
            permission["user_id"] = user_id
        if granted_by is not None:
            permission["granted_by"] = granted_by

        # Update timestamp
        permission["granted_at"] = "2025-12-02T12:00:00"

        # Map permission data to Fibery terminology for output
        output_permission = {
            "permission_id": permission_id,
            "content_id": permission.get("content_id"),
            "content_type": confluence_to_fibery_content_type.get(
                permission.get("content_type"),
                permission.get("content_type")
            ),
            "user_id": permission.get("user_id"),
            "operation": permission.get("operation"),
            "granted_by": permission.get("granted_by"),
            "granted_at": permission.get("granted_at"),
        }

        return json.dumps(output_permission)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "modify_access_permission",
                "description": (
                    "Updates an existing permission record to change access levels or permissions holder. "
                    "Allows modification of: operation (permission type: view, edit, delete, create, admin, restrict_other_users), "
                    "user (permission recipient), or granter (who delegated the permission). "
                    "Use this tool to: escalate/downgrade user access, transfer permission delegation, or correct permission assignments. "
                    "\n"
                    "Important: You can only modify direct permissions explicitly granted on a document; "
                    "inherited permissions from parent documents or containing workspace cannot be modified at the document level. "
                    "To add new permissions, use grant_access_permission; to remove permissions, update operation or use a delete operation if available."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "permission_id": {
                            "type": "string",
                            "description": (
                                "The ID of the permission to alter (required). "
                                "Must reference an existing permission record."
                            ),
                        },
                        "operation": {
                            "type": "string",
                            "description": (
                                "The new operation to set (optional). "
                                "Allowed values: 'view', 'edit', 'delete', 'create', 'admin', 'restrict_other_users'. "
                                "When updated to 'admin', grants all permission types for that content."
                            ),
                        },
                        "user_id": {
                            "type": "string",
                            "description": (
                                "The new user ID to assign the permission to (optional). "
                                "Transfers the permission from current user to specified user."
                            ),
                        },
                        "granted_by": {
                            "type": "string",
                            "description": (
                                "The new granter user ID (optional). "
                                "Updates the record of who delegated this permission."
                            ),
                        },
                    },
                    "required": ["permission_id"],
                },
            },
        }