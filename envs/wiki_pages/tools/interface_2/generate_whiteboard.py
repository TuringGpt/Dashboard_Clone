import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class GenerateWhiteboard(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        title: str,
        created_by: str,
        host_site_id: Optional[str] = None,
        host_page_id: Optional[str] = None,
        content: Optional[str] = None
    ) -> str:
        """
        Create a new whiteboard.
        
        Args:
            data: Environment data
            title: Title of the whiteboard (required)
            created_by: User ID who created the whiteboard (required)
            host_site_id: Space ID where whiteboard is hosted (optional, mutually exclusive with host_page_id)
            host_page_id: Page ID where whiteboard is hosted (optional, mutually exclusive with host_site_id)
            content: Initial content of the whiteboard (optional)
        """
        def generate_id(table: Dict[str, Any]) -> str:
            """Generate a new unique ID for a record."""
            if not table:
                return "1"
            try:
                return str(max(int(k) for k in table.keys()) + 1)
            except ValueError:
                return "1"
        
        # Validate required fields
        if not title or not created_by:
            return json.dumps({
                "error": "Title and created_by are required parameters"
            })
        
        # Validate that either host_site_id or host_page_id is provided, but not both
        if host_site_id and host_page_id:
            return json.dumps({
                "error": "Only one of host_site_id or host_page_id can be provided, not both"
            })
        
        if not host_site_id and not host_page_id:
            return json.dumps({
                "error": "Either host_site_id or host_page_id must be provided"
            })
        
        # Get tables
        whiteboards = data.get("whiteboards", {})
        users = data.get("users", {})
        spaces = data.get("spaces", {})
        pages = data.get("pages", {})
        
        # Validate created_by user exists
        if created_by not in users:
            return json.dumps({
                "error": f"User with ID {created_by} not found"
            })
        
        user = users.get(created_by, {})
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID {created_by} is not active"
            })
        
        # Validate host_site_id exists if provided
        if host_site_id and host_site_id not in spaces:
            return json.dumps({
                "error": f"Space with ID {host_site_id} not found"
            })
        
        # Validate host_page_id exists if provided
        if host_page_id and host_page_id not in pages:
            return json.dumps({
                "error": f"Page with ID {host_page_id} not found"
            })
        
        # Generate new whiteboard ID
        whiteboard_id = generate_id(whiteboards)
        
        # Create whiteboard record
        whiteboard = {
            "whiteboard_id": whiteboard_id,
            "title": title,
            "host_space_id": host_site_id,
            "host_page_id": host_page_id,
            "content": content or "",
            "status": "current",
            "created_by": created_by,
            "created_at": "2025-12-02T12:00:00",
            "updated_by": created_by,
            "updated_at": "2025-12-02T12:00:00"
        }
        
        # Add to data
        whiteboards[whiteboard_id] = whiteboard
        
        return json.dumps({
            "whiteboard_id": whiteboard_id,
            "title": title,
            "host_site_id": host_site_id,
            "host_page_id": host_page_id,
            "content": content or "",
            "status": "current",
            "created_by": created_by,
            "created_at": "2025-12-02T12:00:00",
            "updated_by": created_by,
            "updated_at": "2025-12-02T12:00:00"
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "generate_whiteboard",
                "description": "Create a new whiteboard. Requires title and created_by. Must provide either host_site_id (space ID) or host_page_id (page ID), but not both. Optional content field for initial whiteboard content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the whiteboard"
                        },
                        "created_by": {
                            "type": "string",
                            "description": "User ID who created the whiteboard"
                        },
                        "host_site_id": {
                            "type": "string",
                            "description": "Site ID where whiteboard is hosted (mutually exclusive with host_page_id)"
                        },
                        "host_page_id": {
                            "type": "string",
                            "description": "Page ID where whiteboard is hosted (mutually exclusive with host_site_id)"
                        },
                        "content": {
                            "type": "string",
                            "description": "Initial content of the whiteboard"
                        }
                    },
                    "required": ["title", "created_by"]
                }
            }
        }
