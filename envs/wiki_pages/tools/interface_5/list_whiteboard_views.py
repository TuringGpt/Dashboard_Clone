import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class ListWhiteboardViews(Tool):
    """Retrieve whiteboard metadata, optionally filtered by title, doc, page, or status."""

    @staticmethod
    def invoke(
        data: Dict[str, Any],
        whiteboard_id: Optional[str] = None,
        title: Optional[str] = None,
        doc_id: Optional[str] = None,
        host_page_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})

        whiteboards = data.get("whiteboards", {})
        if not isinstance(whiteboards, dict):
            return json.dumps({"success": False, "error": "Corrupted whiteboards store"})

        def format_record(record_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
            payload = dict(record)
            payload["whiteboard_id"] = record_id
            host_doc_id = payload.pop("host_space_id", None)
            if host_doc_id:
                payload["doc_id"] = host_doc_id
            return payload

        if whiteboard_id:
            record = whiteboards.get(whiteboard_id)
            if not record:
                return json.dumps({"success": False, "error": f"Whiteboard '{whiteboard_id}' not found"})
            return json.dumps({"success": True, "whiteboard": format_record(whiteboard_id, record)})

        filters = {}
        if title:
            filters["title"] = title
        if doc_id:
            filters["host_space_id"] = doc_id
        if host_page_id:
            filters["host_page_id"] = host_page_id
        if status:
            filters["status"] = status

        matches = []
        for record_id, record in whiteboards.items():
            match = True
            for key, value in filters.items():
                if record.get(key) != value:
                    match = False
                    break
            if match:
                matches.append(format_record(record_id, record))

        if not matches:
            return json.dumps({"success": False, "error": "No whiteboards found matching the criteria"})
        return json.dumps({"success": True, "whiteboards": matches, "count": len(matches)})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_whiteboard_views",
                "description": "Retrieve whiteboard metadata by ID or via filters (title, doc, page, status).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "whiteboard_id": {"type": "string", "description": "Specific whiteboard identifier."},
                        "title": {"type": "string", "description": "Exact title match."},
                        "doc_id": {"type": "string", "description": "Doc identifier."},
                        "host_page_id": {"type": "string", "description": "Page hosting the whiteboard."},
                        "status": {"type": "string", "description": "Whiteboard status filter."},
                    },
                    "required": [],
                },
            },
        }
