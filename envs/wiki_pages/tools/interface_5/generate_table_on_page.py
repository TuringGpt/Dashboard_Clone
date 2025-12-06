import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class GenerateTableOnPage(Tool):
    """Create a table (database in confluence) under a specific page within a doc."""

    @staticmethod
    def invoke(
        data: Dict[str, Any],
        title: str,
        host_page_id: str,
        description: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(title, str) or not title.strip():
            return json.dumps({"success": False, "error": "title must be a non-empty string"})
        if not isinstance(created_by, str) or not created_by.strip():
            return json.dumps({"success": False, "error": "created_by must be provided"})
        if not isinstance(host_page_id, str) or not host_page_id.strip():
            return json.dumps({"success": False, "error": "host_page_id must be provided"})

        databases = data.setdefault("databases", {})
        pages = data.setdefault("pages", {})
        spaces = data.setdefault("spaces", {})
        users = data.setdefault("users", {})
        if not all(isinstance(obj, dict) for obj in (databases, pages, spaces, users)):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        if created_by not in users:
            return json.dumps({"success": False, "error": f"User '{created_by}' not found"})

        host_page = pages.get(host_page_id)
        if not host_page:
            return json.dumps({"success": False, "error": f"Host page '{host_page_id}' not found"})
        host_space_id = host_page.get("space_id") or host_page.get("doc_id")
        if host_space_id and host_space_id not in spaces:
            return json.dumps({"success": False, "error": "Host page refers to unknown doc"})

        desired_status = status or "current"
        allowed_status = {"current", "archived", "deleted"}
        if desired_status not in allowed_status:
            return json.dumps({"success": False, "error": "status must be current, archived, or deleted"})

        def next_id(table: Dict[str, Any]) -> str:
            numeric = []
            for key in table.keys():
                try:
                    numeric.append(int(key))
                except (TypeError, ValueError):
                    continue
            return str(max(numeric, default=0) + 1)

        table_id = next_id(databases)
        timestamp = "2025-12-02T12:00:00"
        record = {
            "database_id": table_id,
            "title": title.strip(),
            "host_page_id": host_page_id,
            "description": description,
            "status": desired_status,
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp,
        }
        databases[table_id] = record

        response_record = dict(record)
        response_record["table_id"] = response_record.pop("database_id", table_id)
        return json.dumps({"success": True, "table": response_record})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "generate_table_on_page",
                "description": "Create a table  hosted on a given page.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Table name."},
                        "host_page_id": {
                            "type": "string",
                            "description": "Page hosting the table (required).",
                        },
                        "description": {"type": "string", "description": "Optional description."},
                        "status": {
                            "type": "string",
                            "description": "Lifecycle status (current, archived, deleted). Defaults to current.",
                        },
                        "created_by": {"type": "string", "description": "User ID creating the table."},
                    },
                    "required": ["title", "host_page_id", "created_by"],
                },
            },
        }
