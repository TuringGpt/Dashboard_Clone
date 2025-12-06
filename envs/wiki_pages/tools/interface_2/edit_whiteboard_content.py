import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class EditWhiteboardContent(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        whiteboard_id: str,
        updated_by: str,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> str:
        """
        Edit an existing whiteboard.
        
        Args:
            data: Environment data
            whiteboard_id: ID of the whiteboard to edit (required)
            updated_by: User ID who is updating the whiteboard (required)
            title: New title for the whiteboard (optional)
            content: New content for the whiteboard (optional)
        """
        # Get tables
        whiteboards = data.get("whiteboards", {})
        users = data.get("users", {})
        
        # Validate required fields
        if not whiteboard_id or not updated_by:
            return json.dumps({
                "error": "whiteboard_id and updated_by are required parameters"
            })
        
        # Validate whiteboard exists
        if whiteboard_id not in whiteboards:
            return json.dumps({
                "error": f"Whiteboard with ID {whiteboard_id} not found"
            })
        
        # Validate updated_by user exists
        if updated_by not in users:
            return json.dumps({
                "error": f"User with ID {updated_by} not found"
            })
        
        # Check if at least one field to update is provided
        if title is None and content is None:
            return json.dumps({
                "error": "At least one of title or content must be provided for update"
            })
        
        # Get current whiteboard
        whiteboard = whiteboards[whiteboard_id].copy()
        
        # Update fields if provided
        if title is not None:
            whiteboard["title"] = title
        
        if content is not None:
            whiteboard["content"] = content
        
        # Update metadata
        whiteboard["updated_by"] = updated_by
        whiteboard["updated_at"] = "2025-10-01T00:00:00"
        
        # Save back to data
        whiteboards[whiteboard_id] = whiteboard
        
        return json.dumps(whiteboard)
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "edit_whiteboard_content",
                "description": "Edit an existing whiteboard. Requires whiteboard_id and updated_by. At least one of title or content must be provided for update.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "whiteboard_id": {
                            "type": "string",
                            "description": "ID of the whiteboard to edit"
                        },
                        "updated_by": {
                            "type": "string",
                            "description": "User ID who is updating the whiteboard"
                        },
                        "title": {
                            "type": "string",
                            "description": "New title for the whiteboard"
                        },
                        "content": {
                            "type": "string",
                            "description": "New content for the whiteboard"
                        }
                    },
                    "required": ["whiteboard_id", "updated_by"]
                }
            }
        }
