import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class RemoveList(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        list_id: str
    ) -> str:
        """
        Remove a list (ClickUp logic).
        """
        databases = data.get("databases", {})
        
        # Validate required parameters
        if not list_id:
            return json.dumps({
                "success": False,
                "error": "Missing required parameter: list_id"
            })
        
        # Validate list exists
        if list_id not in databases:
            return json.dumps({
                "success": False,
                "error": f"List with ID '{list_id}' not found"
            })
        
        # Delete the list
        deleted_list = databases.pop(list_id)
        
        # Map database fields to interface fields
        response_list = {
            "list_id": deleted_list.get("database_id"),
            "title": deleted_list.get("title"),
            "host_space_id": deleted_list.get("host_space_id"),
            "host_doc_id": deleted_list.get("host_page_id"),
            "description": deleted_list.get("description"),
            "status": deleted_list.get("status"),
            "created_by": deleted_list.get("created_by"),
            "created_at": deleted_list.get("created_at"),
            "updated_by": deleted_list.get("updated_by"),
            "updated_at": deleted_list.get("updated_at")
        }
        
        return json.dumps({
            "success": True,
            "message": f"List with ID '{list_id}' has been removed",
            "deleted_list": response_list
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "remove_list", 
                "description": "Permanently delete a list from the system by list_id",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "list_id": {
                            "type": "string",
                            "description": "ID of the list to remove"
                        }
                    },
                    "required": ["list_id"]
                }
            }
        }

