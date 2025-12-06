import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class RemoveDatatype(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        type_id: str,
        deleted_by: str,
    ) -> str:
        """
        Permanently deletes a type (database) record.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not type_id or not deleted_by:
            return json.dumps({
                "error": "Missing required parameters: type_id and deleted_by are required"
            })

        type_id = str(type_id)
        deleted_by = str(deleted_by)

        # Access Confluence DB (databases table)
        databases = data.get("databases", {})
        if type_id not in databases:
            return json.dumps({"error": f"Type with ID '{type_id}' not found"})

        # Validate deleted_by user exists
        users = data.get("users", {})
        if deleted_by not in users:
            return json.dumps({"error": f"User with ID '{deleted_by}' not found"})

        # Remove from data (hard delete)
        deleted_database = databases.pop(type_id)
        
        # Return with Fibery naming
        output_type = {
            "type_id": deleted_database.get("database_id", type_id),
            "title": deleted_database.get("title"),
            "host_workspace_id": deleted_database.get("host_space_id"),
            "host_document_id": deleted_database.get("host_page_id"),
            "description": deleted_database.get("description"),
            "status": deleted_database.get("status"),
            "created_by": deleted_database.get("created_by"),
            "created_at": deleted_database.get("created_at"),
            "updated_by": deleted_database.get("updated_by"),
            "updated_at": deleted_database.get("updated_at"),
            "_deleted": True,
            "_deleted_by": deleted_by,
        }
        return json.dumps(output_type)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "remove_datatype",
                "description": (
                    """Permanently deletes a datatype (database) definition from the wiki.
This operation performs hard delete and cannot be reversed or recovered.
Prerequisites: The datatype must have no active records AND no embed blocks referencing it - delete/reassign these first.
Deletion also removes all associated data records stored in the datatype.
Use this tool only when certain the datatype is no longer needed and its data can be permanently discarded.
Important: Embedded references (smart links) to this datatype in documents become broken links after deletion."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type_id": {
                            "type": "string",
                            "description": (
                                "The ID of the type to remove (required)."
                            ),
                        },
                        "deleted_by": {
                            "type": "string",
                            "description": (
                                "The user ID of the person performing the deletion (required)."
                            ),
                        },
                    },
                    "required": ["type_id", "deleted_by"],
                },
            },
        }
