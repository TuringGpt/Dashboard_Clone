import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool


class GetUserProfile(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Retrieve user details from the Confluence database.
        Maps SharePoint user queries to Confluence users table.
        """
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data format"})

        users = data.get("users", {})
        results = []

        for uid, user_data in users.items():
            match = True

            if user_id and uid != user_id:
                match = False
            if email and user_data.get("email") != email:
                match = False
            if status and user_data.get("status") != status:
                match = False

            if match:
                results.append(
                    {
                        "user_id": uid,
                        "email": user_data.get("email"),
                        "display_name": user_data.get("display_name"),
                        "status": user_data.get("status"),
                        "created_at": user_data.get("created_at"),
                        "updated_at": user_data.get("updated_at"),
                    }
                )

        return json.dumps({"success": True, "count": len(results), "users": results})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_user_profile",
                "description": "Retrieve user details. Filters by user_id,\
                    email, or status ('active', 'inactive', 'deactivated').\
                    Returns user information including user_id, email,\
                    display_name, status, created_at, and updated_at.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Unique user identifier",
                        },
                        "email": {
                            "type": "string",
                            "description": "User email address",
                        },
                        "status": {
                            "type": "string",
                            "description": "The state of the user in the system E.g. status: 'active', 'inactive', 'deactivated'",
                        },
                    },
                    "required": [],
                },
            },
        }
