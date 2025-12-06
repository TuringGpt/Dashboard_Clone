import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class ResetInheritanceOnDoc(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        doc_id: str,
        operation: str,
        user_id: str
    ) -> str:
        """
        Reset permission inheritance on a doc by removing specific permission (ClickUp logic).
        """
        permissions_table = data.get("permissions", {})
        pages = data.get("pages", {})
        users = data.get("users", {})
        
        # Validate required parameters
        if not all([doc_id, operation, user_id]):
            return json.dumps({
                "success": False,
                "error": "Missing required parameters: doc_id, operation, and user_id are required"
            })
        
        # Validate doc exists
        if doc_id not in pages:
            return json.dumps({
                "success": False,
                "error": f"Doc with ID '{doc_id}' not found"
            })
        
        # Validate user exists
        if user_id not in users:
            return json.dumps({
                "success": False,
                "error": f"User with ID '{user_id}' not found"
            })
        
        # Validate operation
        valid_operations = ["admin", "edit", "view", "create", "delete", "restrict_other_users"]
        if operation not in valid_operations:
            return json.dumps({
                "success": False,
                "error": f"Invalid operation. Must be one of: {', '.join(valid_operations)}"
            })
        
        # Find and remove the specific permission to reset to inheritance
        permission_to_remove = None
        for perm_id, perm in permissions_table.items():
            if (perm.get("content_id") == doc_id and 
                perm.get("content_type") == "page" and
                perm.get("user_id") == user_id and
                perm.get("operation") == operation):
                permission_to_remove = perm_id
                break
        
        if not permission_to_remove:
            return json.dumps({
                "success": False,
                "error": f"Permission '{operation}' not found for user '{user_id}' on doc '{doc_id}'"
            })
        
        # Remove the permission to reset inheritance
        removed_permission = permissions_table.pop(permission_to_remove)
        
        # Map database fields to interface fields
        response_permission = {
            "permission_id": removed_permission.get("permission_id"),
            "doc_id": removed_permission.get("content_id"),
            "content_type": "doc",
            "user_id": removed_permission.get("user_id"),
            "operation": removed_permission.get("operation"),
            "granted_by": removed_permission.get("granted_by"),
            "granted_at": removed_permission.get("granted_at")
        }
        
        return json.dumps({
            "success": True,
            "message": f"Permission '{operation}' reset to inherit from space for user '{user_id}' on doc '{doc_id}'",
            "removed_permission": response_permission
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "reset_inheritance_on_doc",
                "description": "Reset permission inheritance on a doc by removing doc-level permission overrides",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "ID of the doc"
                        },
                        "operation": {
                            "type": "string",
                            "description": "Permission operation to reset: admin, edit, view, create, delete, restrict_other_users",
                            "enum": ["admin", "edit", "view", "create", "delete", "restrict_other_users"]
                        },
                        "user_id": {
                            "type": "string",
                            "description": "ID of the user whose permission will be reset"
                        }
                    },
                    "required": ["doc_id", "operation", "user_id"]
                }
            }
        }

