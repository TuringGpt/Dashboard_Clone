import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class GetDocData(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        doc_id: Optional[str] = None,
        doc_key: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Retrieve doc (space) information.
        Maps Coda docs to Confluence spaces.
        """

        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        spaces = data.get("spaces", {})
        if not isinstance(spaces, dict):
            return json.dumps({"success": False, "error": "Corrupted spaces store"})

        def format_doc(space_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "doc_id": space_id,
                "doc_key": record.get("space_key"),
                "name": record.get("name"),
                "description": record.get("description"),
                "type": record.get("type"),
                "status": record.get("status"),
                "created_by": record.get("created_by"),
                "created_at": record.get("created_at"),
                "updated_at": record.get("updated_at"),
            }

        if doc_id:
            doc = spaces.get(doc_id)
            if not doc:
                return json.dumps({"success": False, "error": f"Doc '{doc_id}' not found"})
            return json.dumps({"success": True, "doc": format_doc(doc_id, doc)})

        filters = {}
        if doc_key:
            filters["space_key"] = doc_key
        if name:
            filters["name"] = name
        if description:
            filters["description"] = description
        if type:
            filters["type"] = type
        if status:
            filters["status"] = status

        if not filters:
            return json.dumps({"success": False, "doc": None, "docs": []})

        matches = []
        for space_id, record in spaces.items():
            if all(record.get(k) == v for k, v in filters.items()):
                matches.append(format_doc(space_id, record))

        if not matches:
            return json.dumps({"success": False, "error": "No docs found matching the criteria"})
        return json.dumps({"success": True, "docs": matches, "count": len(matches)})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_doc_data",
                "description": "Retrieve doc (workspace document) information. Can search by doc_id, doc_key, name, description, type (global, personal), or status (current, archived). Docs are the top-level containers in Coda that hold pages and other content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {"type": "string", "description": "Unique identifier of the doc."},
                        "doc_key": {"type": "string", "description": "Doc key of the Doc."},
                        "name": {"type": "string", "description": "Name of the doc."},
                        "description": {"type": "string", "description": "Doc description."},
                        "type": {
                            "type": "string",
                            "description": "Doc type (allowed: global, personal).",
                        },
                        "status": {
                            "type": "string",
                            "description": "Doc status (allowed: current, archived).",
                        },
                    },
                    "required": [],
                },
            },
        }
