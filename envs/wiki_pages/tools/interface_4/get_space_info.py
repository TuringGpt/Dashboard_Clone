import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class GetSpaceInfo(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        space_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        space_key: Optional[str] = None
    ) -> str:
        """
        Get space info based on filter criteria.
        """
        spaces = data.get("spaces", {})
        results = []
        
        for sid, space in spaces.items():
            match = True
            
            if space_id and sid != space_id:
                match = False
            if space_key and space.get("space_key") != space_key:
                match = False
            if name and space.get("name") != name:
                match = False
            if description and space.get("description") != description:
                match = False
            if type and space.get("type") != type:
                match = False
            if status and space.get("status") != status:
                match = False
            
            if match:
                results.append(space)
        
        return json.dumps({
            "success": True,
            "count": len(results),
            "spaces": results
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_space_info",
                "description": "Get space info based on filter criteria. Returns all spaces that match the specified filters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "space_id": {
                            "type": "string",
                            "description": "Filter by space ID (optional)"
                        },
                        "space_key": {
                            "type": "string",
                            "description": "Filter by space key (optional)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Filter by space name (optional)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Filter by description (optional)"
                        },
                        "type": {
                            "type": "string",
                            "description": "Filter by type: global, personal (optional)"
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status: current, archived (optional)"
                        }
                    },
                    "required": []
                }
            }
        }