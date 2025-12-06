import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteList(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        list_id: str,
        deleted_by: str
    ) -> str:
        """
        Delete (soft delete) a list.
        
        Args:
            data: Environment data
            list_id: ID of the list to delete (required)
            deleted_by: User ID who is deleting the list (required)
        """
        # Get tables
        databases = data.get("databases", {})
        users = data.get("users", {})
        
        # Validate required fields
        if not list_id or not deleted_by:
            return json.dumps({
                "error": "list_id and deleted_by are required parameters"
            })
        
        # Validate database exists
        if list_id not in databases:
            return json.dumps({
                "error": f"List with ID {list_id} not found"
            })
        
        # Validate deleted_by user exists
        if deleted_by not in users:
            return json.dumps({
                "error": f"User with ID {deleted_by} not found"
            })
        
        user = users.get(deleted_by, {})
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID {deleted_by} is not active"
            })
        
        # Get current database
        database = databases[list_id].copy()
        
        # Check if already deleted
        if database.get("status") == "deleted":
            return json.dumps({
                "error": f"List with ID {list_id} is already deleted"
            })
        
        # Update status to deleted (soft delete)
        database["status"] = "deleted"
        database["updated_by"] = deleted_by
        database["updated_at"] = "2025-12-02T12:00:00"
        
        # Save back to data
        databases[list_id] = database
        
        return json.dumps({
            "list_id": list_id,
            "deleted_by": deleted_by,
            "status": "deleted"
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_list",
                "description": "Delete a list. Requires list_id and deleted_by.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "list_id": {
                            "type": "string",
                            "description": "ID of the list to delete"
                        },
                        "deleted_by": {
                            "type": "string",
                            "description": "User ID who is deleting the list"
                        }
                    },
                    "required": ["list_id", "deleted_by"]
                }
            }
        }
