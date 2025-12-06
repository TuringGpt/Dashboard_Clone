import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class FindUserRecord(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        status: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> str:
        """
        Find user record(s) based on filter criteria.
        """
        users = data.get("users", {})
        results = []
        
        for uid, user in users.items():
            match = True
            
            if user_id and uid != user_id:
                match = False
            if email and user.get("email") != email:
                match = False
            if status and user.get("status") != status:
                match = False
            if display_name and user.get("display_name") != display_name:
                match = False

            if match:
                results.append(user)

        return json.dumps({
            "success": True, 
            "count": len(results), 
            "users": results
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "find_user_record", 
                "description": "Find user records based on filter criteria. Returns all users that match the specified filters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Filter by user ID (optional)",
                        },
                        "email": {
                            "type": "string",
                            "description": "Filter by email address (optional)",
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status: active, inactive, deactivated (optional)",
                        },
                        "display_name": {
                            "type": "string",
                            "description": "Filter by display name (optional)",
                        },
                    },
                    "required": [],
                },
            },
        }