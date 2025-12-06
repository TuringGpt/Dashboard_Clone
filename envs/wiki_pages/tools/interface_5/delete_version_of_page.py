import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteVersionOfPage(Tool):
    """Delete a specific page version if it belongs to the supplied page."""

    @staticmethod
    def invoke(data: Dict[str, Any], page_version_id: str, page_id: str) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(page_version_id, str) or not page_version_id.strip():
            return json.dumps(
                {"success": False, "error": "page_version_id must be provided"}
            )
        if not isinstance(page_id, str) or not page_id.strip():
            return json.dumps({"success": False, "error": "page_id must be provided"})

        page_versions = data.get("page_versions", {})
        if not isinstance(page_versions, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        version = page_versions.get(page_version_id)
        if not version:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Page version '{page_version_id}' not found",
                }
            )

        if version.get("page_id") != page_id:
            return json.dumps(
                {
                    "success": False,
                    "error": "Page version does not belong to the specified page",
                }
            )

        removed = page_versions.pop(page_version_id)
        removed["deleted_at"] = "2025-12-02T12:00:00"
        return json.dumps({"success": True, "page_version": removed})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_version_of_page",
                "description": "Delete a page version by ID corresponding to a page.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_version_id": {
                            "type": "string",
                            "description": "Id of the page version to remove.",
                        },
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page whose version should be removed.",
                        },
                    },
                    "required": ["page_version_id", "page_id"],
                },
            },
        }
