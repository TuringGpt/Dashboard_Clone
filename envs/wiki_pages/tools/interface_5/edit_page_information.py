import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class EditPageInformation(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        page_id: str,
        title: Optional[str] = None,
        doc_id: Optional[str] = None,
        parent_page_id: Optional[str] = None,
        body_storage: Optional[str] = None,
        status: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> str:
        """
        Update an existing page.
        Maps Coda page updates to Confluence pages.
        """

        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})

        pages = data.get("pages", {})
        spaces = data.get("spaces", {})
        users = data.get("users", {})
        if not all(isinstance(obj, dict) for obj in (pages, spaces, users)):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        page = pages.get(page_id)
        if not page:
            return json.dumps({"success": False, "error": f"Page '{page_id}' not found"})

        if doc_id and doc_id not in spaces:
            return json.dumps({"success": False, "error": f"Doc '{doc_id}' not found"})

        if parent_page_id:
            if parent_page_id not in pages:
                return json.dumps({"success": False, "error": f"Parent page '{parent_page_id}' not found"})
            # Ensure parent is within same doc if both provided
            parent_doc = pages[parent_page_id].get("space_id")
            target_doc = doc_id or page.get("space_id")
            if parent_doc != target_doc:
                return json.dumps({"success": False, "error": "Parent page belongs to a different doc"})

        if updated_by and updated_by not in users:
            return json.dumps({"success": False, "error": f"User '{updated_by}' not found"})

        allowed_status = {"current", "draft", "locked", "archived", "deleted"}
        if status and status not in allowed_status:
            return json.dumps({"success": False, "error": "Invalid status value"})

        timestamp = "2025-12-02T12:00:00"
        if title is not None:
            page["title"] = title
        if doc_id is not None:
            page["space_id"] = doc_id
        if body_storage is not None:
            page["body_storage"] = body_storage
        if status is not None:
            page["status"] = status
        if updated_by is not None:
            page["updated_by"] = updated_by
        page["parent_page_id"] = parent_page_id if parent_page_id else None
        page["updated_at"] = timestamp

        client_payload = dict(page)
        client_payload["doc_id"] = client_payload.pop("space_id", doc_id)

        return json.dumps({"success": True, "page_id": page_id, "page": client_payload})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "edit_page_information",
                "description": "Update an existing page. Can modify title, doc (move to different workspace), parent page, content, status (current, draft, locked, archived, deleted), and updated_by user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Identifier of the page to edit."},
                        "title": {"type": "string", "description": "New title (optional)."},
                        "doc_id": {"type": "string", "description": "Target doc for moves (optional)."},
                        "parent_page_id": {
                            "type": "string",
                            "description": "Parent page identifier (optional). Provide null to make the page a root page.",
                        },
                        "body_storage": {"type": "string", "description": "New page content (optional)."},
                        "status": {
                            "type": "string",
                            "description": "Page status (current, draft, locked, archived, deleted).",
                        },
                        "updated_by": {"type": "string", "description": "User applying the change."},
                    },
                    "required": ["page_id", "updated_by"],
                },
            },
        }
