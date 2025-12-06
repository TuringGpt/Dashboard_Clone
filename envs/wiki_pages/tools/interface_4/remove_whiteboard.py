import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class RemoveWhiteboard(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        whiteboard_id: str
    ) -> str:
        """
        Erase a whiteboard (ClickUp logic).
        """
        whiteboards = data.get("whiteboards", {})
        
        # Validate required parameters
        if not whiteboard_id:
            return json.dumps({
                "success": False,
                "error": "Missing required parameter: whiteboard_id"
            })
        
        # Validate whiteboard exists
        if whiteboard_id not in whiteboards:
            return json.dumps({
                "success": False,
                "error": f"Whiteboard with ID '{whiteboard_id}' not found"
            })
        
        # Delete the whiteboard
        deleted_whiteboard = whiteboards.pop(whiteboard_id)
        
        # Map database fields to interface fields
        response_whiteboard = {
            "whiteboard_id": deleted_whiteboard.get("whiteboard_id"),
            "title": deleted_whiteboard.get("title"),
            "host_space_id": deleted_whiteboard.get("host_space_id"),
            "host_doc_id": deleted_whiteboard.get("host_page_id"),
            "content": deleted_whiteboard.get("content"),
            "status": deleted_whiteboard.get("status"),
            "created_by": deleted_whiteboard.get("created_by"),
            "created_at": deleted_whiteboard.get("created_at"),
            "updated_by": deleted_whiteboard.get("updated_by"),
            "updated_at": deleted_whiteboard.get("updated_at")
        }
        
        return json.dumps({
            "success": True,
            "message": f"Whiteboard with ID '{whiteboard_id}' has been erased",
            "deleted_whiteboard": response_whiteboard
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "remove_whiteboard", 
                "description": "Permanently delete a whiteboard from the system by whiteboard_id",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "whiteboard_id": {
                            "type": "string",
                            "description": "ID of the whiteboard to erase"
                        }
                    },
                    "required": ["whiteboard_id"]
                }
            }
        }

