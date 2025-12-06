import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class RetrieveWhiteboard(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        whiteboard_id: Optional[str] = None,
        host_page_id: Optional[str] = None,
        host_site_id: Optional[str] = None
    ) -> str:
        """
        Get whiteboard(s) by ID, host page, or host space.
        
        Args:
            data: Environment data
            whiteboard_id: ID of specific whiteboard to retrieve (optional)
            host_page_id: Page ID to get whiteboards hosted on that page (optional)
            host_site_id: Space ID to get whiteboards hosted in that space (optional)
        """
        # Get tables
        whiteboards = data.get("whiteboards", {})
        pages = data.get("pages", {})
        spaces = data.get("spaces", {})
        
        # Validate that at least one parameter is provided
        if whiteboard_id is None and host_page_id is None and host_site_id is None:
            return json.dumps({
                "error": "At least one of whiteboard_id, host_page_id, or host_site_id must be provided"
            })
        
        # If whiteboard_id is provided, get specific whiteboard
        if whiteboard_id:
            if whiteboard_id not in whiteboards:
                return json.dumps({
                    "error": f"Whiteboard with ID {whiteboard_id} not found"
                })
            
            whiteboard = whiteboards[whiteboard_id]
            
            # Check if whiteboard is not deleted
            if whiteboard.get("status") == "deleted":
                return json.dumps({
                    "error": f"Whiteboard with ID {whiteboard_id} has been deleted"
                })
            
            return json.dumps({
                "whiteboard": whiteboard,
                "count": 1
            })
        
        # Otherwise, filter by host_page_id or host_site_id
        results = []
        
        for wb_id, whiteboard in whiteboards.items():
            # Skip deleted whiteboards
            if whiteboard.get("status") == "deleted":
                continue
            
            match = True
            
            # Filter by host_page_id if provided
            if host_page_id and whiteboard.get("host_page_id") != host_page_id:
                match = False
            
            # Filter by host_site_id if provided
            if host_site_id and whiteboard.get("host_space_id") != host_site_id:
                match = False
            
            if match:
                results.append(whiteboard)
        
        if not results:
            return json.dumps({
                "error": "No whiteboards found matching the criteria",
                "count": 0,
                "results": []
            })
        
        return json.dumps({
            "count": len(results),
            "results": results
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "retrieve_whiteboard",
                "description": "Get whiteboard(s) by ID, host page, or host space. At least one parameter must be provided. If whiteboard_id is provided, returns specific whiteboard. If host_page_id or host_site_id are provided, returns all whiteboards hosted on that page or in that space.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "whiteboard_id": {
                            "type": "string",
                            "description": "ID of specific whiteboard to retrieve"
                        },
                        "host_page_id": {
                            "type": "string",
                            "description": "Page ID to get whiteboards hosted on that page"
                        },
                        "host_site_id": {
                            "type": "string",
                            "description": "Space ID to get whiteboards hosted in that space"
                        }
                    }
                }
            }
        }
