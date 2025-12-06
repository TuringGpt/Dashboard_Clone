import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool


class DiscardWhiteboard(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        whiteboard_id: str,
        deleted_by: str
    ) -> str:
        """
        Delete a whiteboard from the database.
        """
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data format"})

        whiteboards = data.get("whiteboards", {})
        users = data.get("users", {})

        # Validate required fields
        if not all([whiteboard_id, deleted_by]):
            return json.dumps(
                {
                    "success": False,
                    "error": "Missing required parameters: whiteboard_id, deleted_by",
                }
            )

        # Validate whiteboard exists
        if whiteboard_id not in whiteboards:
            return json.dumps(
                {"success": False, "error": f"Whiteboard with ID '{whiteboard_id}' not found"}
            )

        # Validate user exists
        if deleted_by not in users:
            return json.dumps(
                {"success": False, "error": f"User with ID '{deleted_by}' not found"}
            )

        # Perform deletion
        del whiteboards[whiteboard_id]

        return json.dumps({"success": True, "message": f"Whiteboard '{whiteboard_id}' deleted successfully"})


    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "discard_whiteboard",
                "description": "Delete a whiteboard by its ID. Requires whiteboard_id and deleted_by (user ID).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "whiteboard_id": {
                            "type": "string",
                            "description": "Unique whiteboard identifier",
                        },
                        "deleted_by": {
                            "type": "string",
                            "description": "User ID performing the deletion",
                        },
                    
                    },
                    "required": ["whiteboard_id", "deleted_by"],
                },
        }
        }