import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class AlterDatatype(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        type_id: str,
        updated_by: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Alters an existing type (database) record.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not type_id or not updated_by:
            return json.dumps({
                "error": "Missing required parameters: type_id and updated_by are required"
            })

        type_id = str(type_id)
        updated_by = str(updated_by)

        # Access Confluence DB (databases table)
        databases = data.get("databases", {})
        if type_id not in databases:
            return json.dumps({"error": f"Type with ID '{type_id}' not found"})

        # Validate updated_by user exists
        users = data.get("users", {})
        if updated_by not in users:
            return json.dumps({"error": f"User with ID '{updated_by}' not found"})

        database = databases[type_id]

        # Validate status if provided
        if status is not None:
            allowed_statuses = ["current", "archived", "deleted"]
            if status not in allowed_statuses:
                return json.dumps({
                    "error": f"Invalid status. Allowed values: {', '.join(allowed_statuses)}"
                })

        # Update fields if provided
        if title is not None:
            database["title"] = title
        if description is not None:
            database["description"] = description
        if status is not None:
            database["status"] = status

        # Update metadata
        database["updated_by"] = updated_by
        database["updated_at"] = "2025-12-02T12:00:00"

        # Return with Fibery naming
        output_type = {
            "type_id": database.get("database_id", type_id),
            "title": database.get("title"),
            "host_workspace_id": database.get("host_space_id"),
            "host_document_id": database.get("host_page_id"),
            "description": database.get("description"),
            "status": database.get("status"),
            "created_by": database.get("created_by"),
            "created_at": database.get("created_at"),
            "updated_by": database.get("updated_by"),
            "updated_at": database.get("updated_at"),
        }

        return json.dumps(output_type)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "alter_datatype",
                "description": (
                    """Updates an existing datatype (database) definition.
                    Allows modification of datatype properties including title, description, and status.
                    Use this tool when you need to change the name, details, or operational status of a structured data container.
                    Datatypes are reusable data structures that organize information in wiki workspaces."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type_id": {
                            "type": "string",
                            "description": (
                                "The ID of the type to alter (required)."
                            ),
                        },
                        "updated_by": {
                            "type": "string",
                            "description": (
                                "The user ID of the person making the update (required)."
                            ),
                        },
                        "title": {
                            "type": "string",
                            "description": (
                                "The new title for the type (optional)."
                            ),
                        },
                        "description": {
                            "type": "string",
                            "description": (
                                "The new description for the type (optional)."
                            ),
                        },
                        "status": {
                            "type": "string",
                            "description": (
                                "The new status for the type (optional). "
                                "Allowed values: 'current', 'archived', 'deleted'."
                            ),
                        },
                    },
                    "required": ["type_id", "updated_by"],
                },
            },
        }

