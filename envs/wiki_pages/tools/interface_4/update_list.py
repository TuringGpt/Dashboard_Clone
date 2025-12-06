import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class UpdateList(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        list_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        updated_by: str = None
    ) -> str:
        """
        Edit an existing list (ClickUp logic).
        """
        timestamp = "2025-12-02T12:00:00"
        databases = data.get("databases", {})
        users = data.get("users", {})
        
        # Validate required parameters
        if not list_id or not updated_by:
            return json.dumps({
                "success": False,
                "error": "Missing required parameters: list_id and updated_by are required"
            })
        
        # Validate list exists
        if list_id not in databases:
            return json.dumps({
                "success": False,
                "error": f"List with ID '{list_id}' not found"
            })
        
        # Validate user exists
        if updated_by not in users:
            return json.dumps({
                "success": False,
                "error": f"User with ID '{updated_by}' not found"
            })
        
        user = users[updated_by]
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID '{updated_by}' is not active"
            })
        
        # Validate status if provided
        valid_statuses = ["current", "archived", "deleted"]
        if status and status not in valid_statuses:
            return json.dumps({
                "success": False,
                "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            })
        
        # Update the list
        list_obj = databases[list_id]
        
        if title is not None:
            list_obj["title"] = title
        if description is not None:
            list_obj["description"] = description
        if status is not None:
            list_obj["status"] = status
        
        list_obj["updated_by"] = updated_by
        list_obj["updated_at"] = timestamp
        
        # Map database fields to interface fields
        response_list = {
            "list_id": list_obj.get("database_id"),
            "title": list_obj.get("title"),
            "host_space_id": list_obj.get("host_space_id"),
            "host_doc_id": list_obj.get("host_page_id"),
            "description": list_obj.get("description"),
            "status": list_obj.get("status"),
            "created_by": list_obj.get("created_by"),
            "created_at": list_obj.get("created_at"),
            "updated_by": list_obj.get("updated_by"),
            "updated_at": list_obj.get("updated_at")
        }
        
        return json.dumps({
            "success": True,
            "list": response_list
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "update_list", 
                "description": "Update an existing list's properties such as title, description, or status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "list_id": {
                            "type": "string",
                            "description": "ID of the list to edit"
                        },
                        "title": {
                            "type": "string",
                            "description": "New title for the list (optional)"
                        },
                        "description": {
                            "type": "string",
                            "description": "New description for the list (optional)"
                        },
                        "status": {
                            "type": "string",
                            "description": "New status: current, archived, deleted (optional)",
                            "enum": ["current", "archived", "deleted"]
                        },
                        "updated_by": {
                            "type": "string",
                            "description": "User ID of the person updating the list"
                        }
                    },
                    "required": ["list_id", "updated_by"]
                }
            }
        }

