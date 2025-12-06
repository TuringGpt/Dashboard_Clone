import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class CreateList(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        fields: Dict[str, Any]
    ) -> str:
        """
        Add a new list in the specified space (ClickUp logic).
        Wraps arguments in a 'fields' dictionary as per documentation.
        """
        # Unwrap fields
        space_id = fields.get("space_id")
        title = fields.get("title")
        description = fields.get("description")
        created_by = fields.get("created_by")
        
        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)
        
        timestamp = "2025-12-02T12:00:00"
        databases = data.get("databases", {})
        spaces = data.get("spaces", {})
        users = data.get("users", {})
        
        # Validate required parameters
        if not all([space_id, title, created_by]):
            return json.dumps({
                "success": False,
                "error": "Missing required fields in 'fields' dict: space_id, title, and created_by are required"
            })
        
        # Validate space exists
        if space_id not in spaces:
            return json.dumps({
                "success": False,
                "error": f"Space with ID '{space_id}' not found"
            })
        
        # Validate user exists
        if created_by not in users:
            return json.dumps({
                "success": False,
                "error": f"User with ID '{created_by}' not found"
            })
        
        user = users[created_by]
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID '{created_by}' is not active"
            })
        
        # Generate new list (database) ID
        new_list_id = generate_id(databases)
        
        # Create new list for database (using database field names)
        db_list = {
            "database_id": new_list_id,
            "title": title,
            "host_space_id": space_id,
            "host_page_id": None,
            "description": description,
            "status": "current",
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp
        }
        
        databases[new_list_id] = db_list
        
        # Create response object with interface field names
        response_list = {
            "list_id": new_list_id,
            "title": title,
            "host_space_id": space_id,
            "host_doc_id": None,
            "description": description,
            "status": "current",
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp
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
                "name": "create_list", 
                "description": "Create a new list in a specified space. Requires a 'fields' object containing space_id, title, and created_by",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "properties": {
                                "space_id": {
                                    "type": "string",
                                    "description": "ID of the space where the list will be created"
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Title of the list"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Description of the list (optional)"
                                },
                                "created_by": {
                                    "type": "string",
                                    "description": "User ID of the list creator"
                                }
                            },
                            "required": ["space_id", "title", "created_by"]
                        }
                    },
                    "required": ["fields"]
                }
            }
        }

