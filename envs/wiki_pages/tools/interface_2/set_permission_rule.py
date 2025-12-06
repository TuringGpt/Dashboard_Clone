import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class SetPermissionRule(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        filter: Dict[str, str],
    ) -> str:
        """
        Set permissions for a user on a specific content (space or page).
        """
        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)
        
        if not isinstance(data, dict):
            return json.dumps({
                "success": False,
                "error": "Invalid data format"
            })
        
        required_fields = ["content_id", "content_type", "user_id", "operation", "granted_by"]
        missing_fields = [field for field in required_fields if field not in filter]
        if missing_fields:
            return json.dumps({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            })
        
        permissions = data.get("permissions", {})
        users = data.get("users", {})
        pages = data.get("pages", {})
        spaces = data.get("spaces", {})
        
        content_id = filter["content_id"]
        content_type = filter["content_type"]
        user_id = filter["user_id"]
        operation = filter["operation"]
        granted_by = filter["granted_by"]
        
        if content_type not in ["space", "page"]:
            return json.dumps({
                "success": False,
                "error": "content_type must be 'space' or 'page'"
            })
        
        if user_id not in users:
            return json.dumps({
                "success": False,
                "error": f"User with ID {user_id} not found"
            })
        
        user = users.get(user_id, {})
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID {user_id} is not active"
            })
        
        if granted_by not in users:
            return json.dumps({
                "success": False,
                "error": f"User with ID {granted_by} not found"
            })
        
        user = users.get(granted_by, {})
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID {granted_by} is not active"
            })
        
        if content_type == "page" and content_id not in pages:
            return json.dumps({
                "success": False,
                "error": f"Page with ID {content_id} not found"
            })
        
        if content_type == "space" and content_id not in spaces:
            return json.dumps({
                "success": False,
                "error": f"Site with ID {content_id} not found"
            })
        
        valid_operations = ["view", "edit", "delete", "create", "admin", "restrict_other_users"]
        if operation not in valid_operations:
            return json.dumps({
                "success": False,
                "error": f"Operation must be one of: {', '.join(valid_operations)}"
            })
        
        timestamp = "2025-12-02T12:00:00"
        new_perm_id = generate_id(permissions)
        
        new_permission = {
            "permission_id": new_perm_id,
            "content_id": content_id,
            "content_type": content_type,
            "user_id": user_id,
            "operation": operation,
            "granted_by": granted_by,
            "granted_at": timestamp
        }
        
        permissions[new_perm_id] = new_permission
        
        return json.dumps({
            "content_id": content_id,
            "content_type": "site" if content_type == "space" else "page",
            "user_id": user_id,
            "operation": operation,
            "granted_by": granted_by
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "set_permission_rule",
                "description": "Set permissions for a user on a specific content (site or page). Creates a new permission record granting the specified operation to the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "object",
                            "description": "Permission details object containing content_id, content_type, user_id, operation, and granted_by",
                            "properties": {
                                "content_id": {
                                    "type": "string",
                                    "description": "ID of the content (site or page)"
                                },
                                "content_type": {
                                    "type": "string",
                                    "description": "Type of content: 'site' or 'page'"
                                },
                                "user_id": {
                                    "type": "string",
                                    "description": "User ID to grant permission to"
                                },
                                "operation": {
                                    "type": "string",
                                    "description": "Operation to grant: 'view', 'edit', 'delete', 'create', 'admin', or 'restrict_other_users'"
                                },
                                "granted_by": {
                                    "type": "string",
                                    "description": "User ID of the person granting the permission"
                                }
                            },
                            "required": ["content_id", "content_type", "user_id", "operation", "granted_by"]
                        }
                    },
                    "required": ["filter"]
                }
            }
        }
