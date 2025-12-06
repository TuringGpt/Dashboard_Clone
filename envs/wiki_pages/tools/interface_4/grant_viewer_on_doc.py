import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class GrantViewerOnDoc(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        user_id: str,
        doc_id: str
    ) -> str:
        """
        Grant viewer permission to a user on a doc (ClickUp logic).
        """
        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)
        
        timestamp = "2025-12-02T12:00:00"
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
        
        # Create permission entry for database
        new_perm_id = generate_id(permissions_table)
        
        db_permission = {
            "permission_id": new_perm_id,
            "content_id": doc_id,
            "content_type": "page",
            "user_id": user_id,
            "operation": "view",
            "granted_by": "system",
            "granted_at": timestamp
        }
        
        permissions_table[new_perm_id] = db_permission
        
        # Map database fields to interface fields for response
        response_permission = {
            "permission_id": new_perm_id,
            "doc_id": doc_id,
            "content_type": "doc",
            "user_id": user_id,
            "operation": "view",
            "granted_by": "system",
            "granted_at": timestamp
        }
        
        return json.dumps({
            "success": True,
            "permission": response_permission
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "grant_viewer_on_doc",
                "description": "Grant viewer permission to a user on a doc allowing read-only access",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the user to grant permission to"
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

