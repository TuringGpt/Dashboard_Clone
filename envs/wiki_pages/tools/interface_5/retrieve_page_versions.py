import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class RetrievePageVersions(Tool):
    """Fetch page version snapshots using identifiers or optional filters."""

    @staticmethod
    def invoke(
        data: Dict[str, Any],
        page_version_id: Optional[str] = None,
        page_id: Optional[str] = None,
        version_number: Optional[int] = None,
        title: Optional[str] = None,
    ) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})

        page_versions = data.get("page_versions", {})
        if not isinstance(page_versions, dict):
            return json.dumps({"success": False, "error": "Corrupted page_versions store"})

        def format_record(key: str, record: Dict[str, Any]) -> Dict[str, Any]:
            payload = dict(record)
            payload["page_version_id"] = key
            return payload

        if page_version_id:
            record = page_versions.get(page_version_id)
            if not record:
                return json.dumps({"success": False, "error": f"Page version '{page_version_id}' not found"})
            payload = format_record(page_version_id, record)
            return json.dumps({"success": True, "page_version": payload})

        filters: Dict[str, Any] = {}
        if page_id:
            filters["page_id"] = page_id
        if title:
            filters["title"] = title
        if version_number is not None:
            if not isinstance(version_number, int):
                return json.dumps({"success": False, "error": "version_number must be an integer"})
            filters["version_number"] = version_number

        if not filters:
            return json.dumps({"success": True, "page_versions": []})

        matches = []
        for key, record in page_versions.items():
            match = True
            for filter_key, filter_value in filters.items():
                if record.get(filter_key) != filter_value:
                    match = False
                    break
            if match:
                matches.append(format_record(key, record))

        if not matches:
            return json.dumps({"success": False, "error": "No versions found matching the criteria"})
        return json.dumps({"success": True, "page_versions": matches, "count": len(matches)})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "retrieve_page_versions",
                "description": "Fetch page versions by ID or using optional filters (page, version number, title).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_version_id": {"type": "string", "description": "Specific version identifier."},
                        "page_id": {"type": "string", "description": "Page identifier to pull versions for."},
                        "version_number": {"type": "integer", "description": "Specific version sequence number."},
                        "title": {"type": "string", "description": "Title stored in the version."},
                    },
                    "required": [],
                },
            },
        }
