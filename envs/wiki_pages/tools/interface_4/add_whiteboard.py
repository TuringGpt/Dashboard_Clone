import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class AddWhiteboard(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        title: str,
        created_by: str,
        doc_id: str,
        content: str,
        status: str
    ) -> str:
        """
        Add a new whiteboard to a doc (ClickUp logic).
        """
        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)
        
        timestamp = "2025-12-02T12:00:00"
        whiteboards = data.get("whiteboards", {})
        pages = data.get("pages", {})
        users = data.get("users", {})
        
        # Validate required parameters
        if not all([title, created_by, doc_id, content, status]):
            return json.dumps({
                "success": False,
                "error": "Missing required parameters: title, created_by, doc_id, content, and status are required"
            })
        
        # Validate doc exists
        if doc_id not in pages:
            return json.dumps({
                "success": False,
                "error": f"Doc with ID '{doc_id}' not found"
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
        
        # Validate status
        valid_statuses = ["current", "locked", "archived"]
        if status not in valid_statuses:
            return json.dumps({
                "success": False,
                "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            })
        
        # Generate new whiteboard ID
        new_whiteboard_id = generate_id(whiteboards)
        
        # Create new whiteboard for database (using database field names)
        db_whiteboard = {
            "whiteboard_id": new_whiteboard_id,
            "title": title,
            "host_space_id": None,
            "host_page_id": doc_id,
            "content": content,
            "status": status,
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp
        }
        
        whiteboards[new_whiteboard_id] = db_whiteboard
        
        # Create response object with interface field names
        response_whiteboard = {
            "whiteboard_id": new_whiteboard_id,
            "title": title,
            "host_space_id": None,
            "host_doc_id": doc_id,
            "content": content,
            "status": status,
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp
        }
        
        return json.dumps({
            "success": True,
            "whiteboard": response_whiteboard
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "add_whiteboard", 
                "description": "Add a new whiteboard to a doc with title, content, and status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the whiteboard"
                        },
                        "created_by": {
                            "type": "string",
                            "description": "User ID of the whiteboard creator"
                        },
                        "doc_id": {
                            "type": "string",
                            "description": "ID of the doc where the whiteboard will be created"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content of the whiteboard in JSON format"
                        },
                        "status": {
                            "type": "string",
                            "description": "Status of the whiteboard: current, locked, archived",
                            "enum": ["current", "locked", "archived"]
                        }
                    },
                    "required": ["title", "created_by", "doc_id", "content", "status"]
                }
            }
        }

