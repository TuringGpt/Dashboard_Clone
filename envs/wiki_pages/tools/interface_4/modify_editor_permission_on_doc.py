import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class ModifyEditorPermissionOnDoc(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        user_id: str,
        doc_id: str
    ) -> str:
        """
        Modify editor permission on a doc by revoking it (ClickUp logic).
        """
        permissions_table = data.get("permissions", {})
        pages = data.get("pages", {})
        users = data.get("users", {})
        
        # Validate required parameters
        if not all([doc_id, user_id]):
            return json.dumps({
                "success": False,
                "error": "Missing required parameters: doc_id and user_id are required"
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
        
        # Find and remove the editor permission
        permission_to_remove = None
        for perm_id, perm in permissions_table.items():
            if (perm.get("content_id") == doc_id and 
                perm.get("content_type") == "page" and
                perm.get("user_id") == user_id and
                perm.get("operation") == "edit"):
                permission_to_remove = perm_id
                break
        
        if not permission_to_remove:
            return json.dumps({
                "success": False,
                "error": f"Editor permission not found for user '{user_id}' on doc '{doc_id}'"
            })
        
        # Remove the permission
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
            "message": f"Editor permission revoked for user '{user_id}' on doc '{doc_id}'",
            "removed_permission": response_permission
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "modify_editor_permission_on_doc",
                "description": "Revoke editor permission from a user on a doc",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the user to revoke permission from"
                        },
                        "doc_id": {
                            "type": "string",
                            "description": "ID of the doc"
                        }
                    },
                    "required": ["user_id", "doc_id"]
                }
            }
        }

