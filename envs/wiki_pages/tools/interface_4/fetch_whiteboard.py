import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class FetchWhiteboard(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        whiteboard_id: Optional[str] = None,
        host_doc_id: Optional[str] = None,
        title: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> str:
        """
        Fetch whiteboard(s) based on filter criteria (ClickUp logic).
        """
        whiteboards = data.get("whiteboards", {})
        results = []
        
        for wb_id, whiteboard in whiteboards.items():
            match = True
            
            if whiteboard_id and wb_id != whiteboard_id:
                match = False
            if host_doc_id and whiteboard.get("host_page_id") != host_doc_id:
                match = False
            if title and whiteboard.get("title") != title:
                match = False
            if status and whiteboard.get("status") != status:
                match = False
            if created_by and whiteboard.get("created_by") != created_by:
                match = False
            
            if match:
                # Map database fields to interface fields
                wb = {
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
                results.append(wb)
        
        return json.dumps({
            "success": True,
            "count": len(results),
            "whiteboards": results
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "fetch_whiteboard", 
                "description": "Retrieve whiteboards based on filter criteria such as whiteboard_id, host_doc_id, or status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "whiteboard_id": {
                            "type": "string",
                            "description": "Filter by whiteboard ID (optional)"
                        },
                        "host_doc_id": {
                            "type": "string",
                            "description": "Filter by host doc ID (optional)"
                        },
                        "title": {
                            "type": "string",
                            "description": "Filter by title (optional)"
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status: current, locked, archived (optional)"
                        },
                        "created_by": {
                            "type": "string",
                            "description": "Filter by creator user ID (optional)"
                        }
                    },
                    "required": []
                }
            }
        }

