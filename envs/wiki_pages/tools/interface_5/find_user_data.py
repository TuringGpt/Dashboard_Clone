import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class FindUserData(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        email: Optional[str] = None,
    ) -> str:
        """
        Retrieve user information from the system.
        Maps Coda user queries to Confluence users table.
        """

        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        users = data.get("users", {})
        if not isinstance(users, dict):
            return json.dumps({"success": False, "error": "Corrupted users store"})

        if not user_id and not email:
            return json.dumps({"success": False, "user": None})

        # Prefer direct lookup by ID for speed
        if user_id:
            user = users.get(user_id)
            if not user:
                return json.dumps({"success": False, "error": f"User '{user_id}' not found"})
            if email and user.get("email") != email:
                return json.dumps({"success": False, "error": "User found but email mismatch"})
            return json.dumps({"success": True, "user": {**user, "user_id": user_id}})

        # Search by email only
        for uid, record in users.items():
            if record.get("email") == email:
                return json.dumps({"success": True, "user": {**record, "user_id": uid}})

        return json.dumps({"success": False, "error": "No users found matching the criteria"})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "find_user_data",
                "description": "Retrieve user information from the Coda workspace. Can search by user_id, email, or status (active, inactive, deactivated). Used to verify user existence and status before performing operations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "Unique identifier of the user."},
                        "email": {"type": "string", "description": "Email address of the user."},
                    },
                    "required": [],
                },
            },
        }
