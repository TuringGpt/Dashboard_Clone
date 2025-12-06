import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class ModifyWhiteboard(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        fields: Dict[str, Any]
    ) -> str:
        """
        Modify an existing whiteboard (ClickUp logic).
        Wraps arguments in a 'fields' dictionary as per documentation.
        """
        # Unwrap fields
        whiteboard_id = fields.get("whiteboard_id")
        title = fields.get("title")
        content = fields.get("content")
        updated_by = fields.get("updated_by")
        
        timestamp = "2025-12-02T12:00:00"
        whiteboards = data.get("whiteboards", {})
        users = data.get("users", {})
        
        # Validate required parameters
        if not whiteboard_id or not updated_by:
            return json.dumps({
                "success": False,
                "error": "Missing required fields in 'fields' dict: whiteboard_id and updated_by are required"
            })
        
        # Validate whiteboard exists
        if whiteboard_id not in whiteboards:
            return json.dumps({
                "success": False,
                "error": f"Whiteboard with ID '{whiteboard_id}' not found"
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
        
        # Update the whiteboard
        whiteboard = whiteboards[whiteboard_id]
        
        if title is not None:
            whiteboard["title"] = title
        if content is not None:
            whiteboard["content"] = content
        
        whiteboard["updated_by"] = updated_by
        whiteboard["updated_at"] = timestamp
        
        # Map database fields to interface fields
        response_whiteboard = {
            "whiteboard_id": whiteboard.get("whiteboard_id"),
            "title": whiteboard.get("title"),
            "host_space_id": whiteboard.get("host_space_id"),
            "host_doc_id": whiteboard.get("host_page_id"),
            "content": whiteboard.get("content"),
            "status": whiteboard.get("status"),
            "created_by": whiteboard.get("created_by"),
            "created_at": whiteboard.get("created_at"),
            "updated_by": whiteboard.get("updated_by"),
            "updated_at": whiteboard.get("updated_at")
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
                "name": "modify_whiteboard", 
                "description": "Update an existing whiteboard's title or content. Requires a 'fields' object containing whiteboard_id and updated_by",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "properties": {
                                "whiteboard_id": {
                                    "type": "string",
                                    "description": "ID of the whiteboard to modify"
                                },
                                "title": {
                                    "type": "string",
                                    "description": "New title for the whiteboard (optional)"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "New content for the whiteboard in JSON format (optional)"
                                },
                                "updated_by": {
                                    "type": "string",
                                    "description": "User ID of the person modifying the whiteboard"
                                }
                            },
                            "required": ["whiteboard_id", "updated_by"]
                        }
                    },
                    "required": ["fields"]
                }
            }
        }

