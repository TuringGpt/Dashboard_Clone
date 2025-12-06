import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class InsertWhiteboardView(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        title: str,
        created_by: str,
        host_workspace_id: Optional[str] = None,
        host_document_id: Optional[str] = None,
        content: Optional[str] = None,
        status: str = "current",
    ) -> str:
        """
        Create a new whiteboard view in Fibery.
        Maps to Confluence whiteboards table.
        """

        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)

        timestamp = "2025-12-02T12:00:00"
        whiteboards = data.get("whiteboards", {})
        spaces = data.get("spaces", {})
        pages = data.get("pages", {})
        users = data.get("users", {})

        # Validate that either host_workspace_id OR host_document_id is provided (mutually exclusive)
        if not host_workspace_id and not host_document_id:
            return json.dumps(
                {
                    "success": False,
                    "error": "Either host_workspace_id or host_document_id must be provided",
                }
            )

        if host_workspace_id and host_document_id:
            return json.dumps(
                {
                    "success": False,
                    "error": "Only one of host_workspace_id or host_document_id should be provided",
                }
            )

        # Validate host workspace if provided
        if host_workspace_id:
            if host_workspace_id not in spaces:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Workspace with ID '{host_workspace_id}' not found",
                    }
                )

        # Validate host document if provided
        if host_document_id:
            if host_document_id not in pages:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Document with ID '{host_document_id}' not found",
                    }
                )

        # Validate user exists and is active
        if created_by not in users:
            return json.dumps(
                {"success": False, "error": f"User with ID '{created_by}' not found"}
            )

        user = users[created_by]
        if user.get("status") != "active":
            return json.dumps(
                {
                    "success": False,
                    "error": f"User with ID '{created_by}' is not active",
                }
            )

        # Validate status
        valid_statuses = ["current", "archived", "deleted", "locked"]
        if status not in valid_statuses:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                }
            )

        # Generate new whiteboard ID
        new_whiteboard_id = generate_id(whiteboards)

        # Create new whiteboard
        new_whiteboard = {
            "whiteboard_id": new_whiteboard_id,
            "title": title,
            "host_space_id": host_workspace_id,
            "host_page_id": host_document_id,
            "content": content,
            "status": status,
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp,
        }

        whiteboards[new_whiteboard_id] = new_whiteboard

        return json.dumps(
            {
                "success": True,
                "whiteboard_view_id": new_whiteboard_id,
                "whiteboard_data": new_whiteboard,
            }
        )

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "insert_whiteboard_view",
                "description": "Create a new collaborative whiteboard view. Whiteboards can be hosted at workspace level or document level (mutually exclusive). Status options: 'current', 'archived', 'deleted', 'locked'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the whiteboard (required)",
                        },
                        "created_by": {
                            "type": "string",
                            "description": "User ID of the whiteboard creator (required)",
                        },
                        "host_workspace_id": {
                            "type": "string",
                            "description": "ID of the workspace hosting the whiteboard (optional, mutually exclusive with host_document_id)",
                        },
                        "host_document_id": {
                            "type": "string",
                            "description": "ID of the document hosting the whiteboard (optional, mutually exclusive with host_workspace_id)",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content of the whiteboard (optional)",
                        },
                        "status": {
                            "type": "string",
                            "description": "Whiteboard status: 'current', 'archived', 'deleted', 'locked' (defaults to 'current')",
                            "enum": ["current", "archived", "deleted", "locked"],
                        },
                    },
                    "required": ["title", "created_by"],
                },
            },
        }
