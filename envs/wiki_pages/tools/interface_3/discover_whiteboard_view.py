import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class DiscoverWhiteboardView(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        whiteboard_view_id: Optional[str] = None,
        title: Optional[str] = None,
        host_workspace_id: Optional[str] = None,
        host_document_id: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> str:
        """
        Retrieve whiteboard views based on filters.
        Maps to Confluence whiteboards table.
        
        All inputs and outputs use Fibery terminology:
        - host_workspace_id (not host_space_id)
        - host_document_id (not host_page_id)
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        whiteboards = data.get("whiteboards", {})
        results = []

        for whiteboard_id, whiteboard_data in whiteboards.items():
            match = True

            # Apply filters using Confluence DB field names for internal lookup
            if whiteboard_view_id and whiteboard_id != whiteboard_view_id:
                match = False
            if title and whiteboard_data.get("title") != title:
                match = False
            if (
                host_workspace_id
                and whiteboard_data.get("host_space_id") != host_workspace_id
            ):
                match = False
            if (
                host_document_id
                and whiteboard_data.get("host_page_id") != host_document_id
            ):
                match = False
            if status and whiteboard_data.get("status") != status:
                match = False
            if created_by and whiteboard_data.get("created_by") != created_by:
                match = False
            if updated_by and whiteboard_data.get("updated_by") != updated_by:
                match = False

            if match:
                # Map Confluence DB output to Fibery terminology consistently
                result_record = {
                    "whiteboard_view_id": whiteboard_data.get("whiteboard_id", whiteboard_id),
                    "title": whiteboard_data.get("title"),
                    "host_workspace_id": whiteboard_data.get("host_space_id"),
                    "host_document_id": whiteboard_data.get("host_page_id"),
                    "content": whiteboard_data.get("content"),
                    "status": whiteboard_data.get("status"),
                    "created_by": whiteboard_data.get("created_by"),
                    "created_at": whiteboard_data.get("created_at"),
                    "updated_by": whiteboard_data.get("updated_by"),
                    "updated_at": whiteboard_data.get("updated_at"),
                }
                results.append(result_record)

        return json.dumps({
            "success": True,
            "count": len(results),
            "results": results
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "discover_whiteboard_view",
                "description": (
                    "Retrieve whiteboard views based on filters. "
                    "All parameters are optional filters. "
                    "Status options: 'current', 'archived', 'deleted', 'locked'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "whiteboard_view_id": {
                            "type": "string",
                            "description": "ID of the whiteboard to retrieve (optional)",
                        },
                        "title": {
                            "type": "string",
                            "description": "Filter by whiteboard title (optional)",
                        },
                        "host_workspace_id": {
                            "type": "string",
                            "description": "Filter by hosting workspace ID (optional)",
                        },
                        "host_document_id": {
                            "type": "string",
                            "description": "Filter by hosting document ID (optional)",
                        },
                        "status": {
                            "type": "string",
                            "description": (
                                "Filter by status (optional). "
                                "Allowed values: 'current', 'archived', 'deleted', 'locked'"
                            ),
                            "enum": ["current", "archived", "deleted", "locked"],
                        },
                        "created_by": {
                            "type": "string",
                            "description": "Filter by creator user ID (optional)",
                        },
                        "updated_by": {
                            "type": "string",
                            "description": "Filter by last updater user ID (optional)",
                        },
                    },
                },
            },
        }