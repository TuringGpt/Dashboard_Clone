import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class MakeVersionForPage(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], ref: Dict[str, Any]) -> str:
        """
        Create a new version snapshot of a page.
        Maps to Confluence page_versions table.
        """

        def generate_id(table: Dict[str, Any]) -> str:
            """Generate next integer ID stored as string."""
            if not table:
                return "1"
            numeric_ids = []
            for key in table.keys():
                try:
                    numeric_ids.append(int(key))
                except (TypeError, ValueError):
                    continue
            next_id = max(numeric_ids, default=0) + 1
            return str(next_id)

        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(ref, dict):
            return json.dumps({"success": False, "error": "ref must be an object"})

        page_id = ref.get("page_id")
        title = ref.get("title")
        body_storage = ref.get("body_storage")

        if not isinstance(page_id, str) or not page_id.strip():
            return json.dumps({"success": False, "error": "page_id must be a non-empty string"})
        if not isinstance(title, str) or not title.strip():
            return json.dumps({"success": False, "error": "title must be a non-empty string"})
        if body_storage is not None and not isinstance(body_storage, str):
            return json.dumps({"success": False, "error": "body_storage must be a string if provided"})

        pages = data.get("pages", {})
        page_versions = data.setdefault("page_versions", {})

        if not isinstance(pages, dict) or not isinstance(page_versions, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        page = pages.get(page_id)
        if not page:
            return json.dumps({"success": False, "error": f"Page '{page_id}' not found"})

        existing_versions = [
            version for version in page_versions.values() if version.get("page_id") == page_id
        ]
        version_number = len(existing_versions) + 1

        new_version_id = generate_id(page_versions)
        timestamp = "2025-12-02T12:00:00"
        version_record = {
            "page_version_id": new_version_id,
            "page_id": page_id,
            "version_number": version_number,
            "title": title.strip(),
            "body_storage": body_storage if body_storage is not None else page.get("body_storage"),
            "created_at": timestamp,
        }

        page_versions[new_version_id] = version_record
        return json.dumps({"success": True, "page_version_id": new_version_id, "version": version_record})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "make_version_for_page",
                "description": "Create a new version snapshot of a page. This captures the current state of the page including title and content. Version numbers are automatically incremented.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ref": {
                            "type": "object",
                            "description": "Reference payload describing the page snapshot.",
                            "properties": {
                                "page_id": {
                                    "type": "string",
                                    "description": "Unique identifier of the page to version",
                                },
                                "title": {"type": "string", "description": "Title captured in this version."},
                                "body_storage": {
                                    "type": "string",
                                    "description": "Optional body content to store for the version.",
                                },
                            },
                            "required": ["page_id", "title"],
                        }
                    },
                    "required": ["ref"],
                },
            },
        }
