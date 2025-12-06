import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class AlterWhiteboardView(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        whiteboard_view_id: str,
        updated_by: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Alters an existing whiteboard view record.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not whiteboard_view_id or not updated_by:
            return json.dumps({
                "error": "Missing required parameters: whiteboard_view_id and updated_by are required"
            })

        whiteboard_view_id = str(whiteboard_view_id)
        updated_by = str(updated_by)

        # Access Confluence DB (whiteboards table)
        whiteboards = data.get("whiteboards", {})
        if whiteboard_view_id not in whiteboards:
            return json.dumps({"error": f"Whiteboard view with ID '{whiteboard_view_id}' not found"})

        # Validate updated_by user exists
        users = data.get("users", {})
        if updated_by not in users:
            return json.dumps({"error": f"User with ID '{updated_by}' not found"})

        whiteboard = whiteboards[whiteboard_view_id]

        # Validate status if provided
        if status is not None:
            allowed_statuses = ["current", "archived", "deleted", "locked"]
            if status not in allowed_statuses:
                return json.dumps({
                    "error": f"Invalid status. Allowed values: {', '.join(allowed_statuses)}"
                })

        # Update fields if provided
        if title is not None:
            whiteboard["title"] = title
        if content is not None:
            whiteboard["content"] = content
        if status is not None:
            whiteboard["status"] = status

        # Update metadata
        whiteboard["updated_by"] = updated_by
        whiteboard["updated_at"] = "2025-12-02T12:00:00"

        # Return with Fibery naming
        output_whiteboard = {
            "whiteboard_view_id": whiteboard.get("whiteboard_id", whiteboard_view_id),
            "title": whiteboard.get("title"),
            "host_workspace_id": whiteboard.get("host_space_id"),
            "host_document_id": whiteboard.get("host_page_id"),
            "content": whiteboard.get("content"),
            "status": whiteboard.get("status"),
            "created_by": whiteboard.get("created_by"),
            "created_at": whiteboard.get("created_at"),
            "updated_by": whiteboard.get("updated_by"),
            "updated_at": whiteboard.get("updated_at"),
        }

        return json.dumps(output_whiteboard)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "alter_whiteboard_view",
                "description": (
                    """Updates an existing collaborative whiteboard.
Allows modification of whiteboard properties: display title, canvas content (drawing/data), and status.
Use this tool to rename whiteboards, update whiteboard drawings/content, or change whiteboard status (lock, archive).
Whiteboards are collaborative visual canvases hosted at workspace or document level for brainstorming, diagramming, and real-time collaboration."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "whiteboard_view_id": {
                            "type": "string",
                            "description": (
                                "The ID of the whiteboard view to alter (required)."
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
                                "The new title for the whiteboard view (optional)."
                            ),
                        },
                        "content": {
                            "type": "string",
                            "description": (
                                "The new content/data for the whiteboard view (optional)."
                            ),
                        },
                        "status": {
                            "type": "string",
                            "description": (
                                "The new status for the whiteboard view (optional). "
                                "Allowed values: 'current', 'archived', 'deleted', 'locked'."
                            ),
                        },
                    },
                    "required": ["whiteboard_view_id", "updated_by"],
                },
            },
        }

