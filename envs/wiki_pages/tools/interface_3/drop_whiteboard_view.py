import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DropWhiteboardView(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        fields: Dict[str, str],
    ) -> str:
        """
        Ejects (deletes) a whiteboard view record.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not fields or not isinstance(fields, dict):
            return json.dumps({"error": "Missing required parameter: fields must be a JSON object"})

        whiteboard_view_id = fields.get("whiteboard_view_id")
        deleted_by = fields.get("deleted_by")

        if not whiteboard_view_id or not deleted_by:
            return json.dumps({
                "error": "Missing required parameters: fields.whiteboard_view_id and fields.deleted_by are required"
            })

        whiteboard_view_id = str(whiteboard_view_id)
        deleted_by = str(deleted_by)

        # Access Confluence DB (whiteboards table)
        whiteboards = data.get("whiteboards", {})
        if whiteboard_view_id not in whiteboards:
            return json.dumps({"error": f"Whiteboard view with ID '{whiteboard_view_id}' not found"})

        # Validate deleted_by user exists
        users = data.get("users", {})
        if deleted_by not in users:
            return json.dumps({"error": f"User with ID '{deleted_by}' not found"})

        # Remove from data (hard delete)
        deleted_whiteboard = whiteboards.pop(whiteboard_view_id)
        
        # Return with Fibery naming
        output_whiteboard = {
            "whiteboard_view_id": deleted_whiteboard.get("whiteboard_id", whiteboard_view_id),
            "title": deleted_whiteboard.get("title"),
            "host_workspace_id": deleted_whiteboard.get("host_space_id"),
            "host_document_id": deleted_whiteboard.get("host_page_id"),
            "content": deleted_whiteboard.get("content"),
            "status": deleted_whiteboard.get("status"),
            "created_by": deleted_whiteboard.get("created_by"),
            "created_at": deleted_whiteboard.get("created_at"),
            "updated_by": deleted_whiteboard.get("updated_by"),
            "updated_at": deleted_whiteboard.get("updated_at"),
            "_deleted": True,
            "_deleted_by": deleted_by,
        }
        return json.dumps(output_whiteboard)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "drop_whiteboard_view",
                "description": (
                    """Permanently removes a whiteboard from a workspace or document.
This operation performs a hard delete and cannot be reversed or recovered.
All embed block references to this whiteboard will become broken links.
Use this tool only when confident the whiteboard and all its content should be permanently deleted.
Consider exporting or archiving whiteboard content before deletion if you may need it later.
Note: Embedded references (smart links) to this whiteboard are not automatically cleaned up."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "description": (
                                "The fields for the delete operation (required). "
                                "Must include 'whiteboard_view_id' and 'deleted_by'."
                            ),
                            "properties": {
                                "whiteboard_view_id": {
                                    "type": "string",
                                    "description": "The ID of the whiteboard view to remove (required).",
                                },
                                "deleted_by": {
                                    "type": "string",
                                    "description": "The user ID of the person performing the deletion (required).",
                                },
                            },
                            "required": ["whiteboard_view_id", "deleted_by"],
                        },
                    },
                    "required": ["fields"],
                },
            },
        }
