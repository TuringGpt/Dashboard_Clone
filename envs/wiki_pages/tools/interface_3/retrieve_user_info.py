import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class RetrieveUserInfo(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Retrieve user records with optional filters.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if filters is not None and not isinstance(filters, dict):
            return json.dumps({"error": "filters must be a JSON object if provided"})

        # Access Confluence DB table
        table = data.get("users", {})
        results = []
        effective_filters = filters or {}

        # Convert ID values in filters to strings for consistent comparison
        if effective_filters:
            id_filter_fields = ["user_id"]
            for field in id_filter_fields:
                if field in effective_filters and effective_filters[field] is not None:
                    effective_filters[field] = str(effective_filters[field])

        for record_id, record in table.items():
            if not isinstance(record, dict):
                continue

            match = True
            for key, value in effective_filters.items():
                if key == "user_id":
                    stored_id = record.get("user_id")
                    if str(record_id) != str(value) and str(stored_id) != str(value):
                        match = False
                        break
                else:
                    if record.get(key) != value:
                        match = False
                        break

            if match:
                result_record = record.copy()
                if "user_id" not in result_record:
                    result_record["user_id"] = str(record_id)
                results.append(result_record)

        return json.dumps({
            "entity_type": "users",
            "count": len(results),
            "results": results,
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "retrieve_user_info",
                "description": (
                    "Retrieves user records. "
                    "Users represent individuals who can create, edit, and interact with content. "
                    "Optional filters allow narrowing results by user attributes."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "object",
                            "description": (
                                "Optional JSON object with filter key-value pairs (AND logic). "
                                "Supported fields: user_id, email, status. "
                                "status enum: 'active', 'inactive', 'deactivated'."
                            ),
                            "properties": {
                                "user_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the user to retrieve (e.g., '1', '25').",
                                },
                                "email": {
                                    "type": "string",
                                    "description": "The email address of the user (e.g., 'john@example.com').",
                                },
                                "status": {
                                    "type": "string",
                                    "description": "The status of the user. Allowed values: 'active' (can perform actions), 'inactive' (temporarily disabled), 'deactivated' (permanently disabled).",
                                },
                            },
                        },
                    },
                    "required": [],
                },
            },
        }
