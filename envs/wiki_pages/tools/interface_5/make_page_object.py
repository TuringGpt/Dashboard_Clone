import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class MakePageObject(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        title: str,
        doc_id: str,
        created_by: str,
        parent_page_id: Optional[str] = None,
        body_storage: Optional[str] = None,
        status: Optional[str] = "current",
    ) -> str:
        """
        Create a new page in a doc.
        Maps Coda pages to Confluence pages.
        """

        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})

        pages = data.setdefault("pages", {})
        spaces = data.setdefault("spaces", {})
        users = data.setdefault("users", {})

        if not isinstance(pages, dict) or not isinstance(spaces, dict) or not isinstance(users, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        if not isinstance(title, str) or not title.strip():
            return json.dumps({"success": False, "error": "title must be a non-empty string"})
        normalized_title = title.strip()

        # Validate doc (space) and user existence
        if doc_id not in spaces:
            return json.dumps({"success": False, "error": f"Doc with ID '{doc_id}' not found"})
        if created_by not in users:
            return json.dumps({"success": False, "error": f"User with ID '{created_by}' not found"})

        # Validate parent page if supplied
        if parent_page_id:
            parent = pages.get(parent_page_id)
            if not parent:
                return json.dumps({"success": False, "error": f"Parent page '{parent_page_id}' not found"})
            parent_doc_id = parent.get("space_id") or parent.get("doc_id")
            if parent_doc_id != doc_id:
                return json.dumps({"success": False, "error": "Parent page belongs to a different doc"})

        allowed_status = {"current", "draft", "locked", "archived", "deleted"}
        if status and status not in allowed_status:
            return json.dumps({"success": False, "error": "Invalid status value"})

        for existing in pages.values():
            existing_doc_id = existing.get("space_id") or existing.get("doc_id")
            existing_title = (existing.get("title") or "").strip()
            if existing_doc_id == doc_id and existing_title.lower() == normalized_title.lower():
                return json.dumps({"success": False, "error": "Page title already exists in this doc"})

        def generate_id(table: Dict[str, Any]) -> str:
            """Generate the next numeric string ID."""
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

        new_page_id = generate_id(pages)
        timestamp = "2025-12-02T12:00:00"
        page_record = {
            "page_id": new_page_id,
            "title": normalized_title,
            "space_id": doc_id,
            "parent_page_id": parent_page_id,
            "body_storage": body_storage,
            "status": status or "current",
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp,
        }
        pages[new_page_id] = page_record

        client_payload = dict(page_record)
        client_payload["doc_id"] = client_payload.pop("space_id")

        return json.dumps({"success": True, "page_id": new_page_id, "page": client_payload})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "make_page_object",
                "description": "Create a new page in a doc. Pages can be top-level (within a doc) or sub-pages (children of other pages). Status options: 'current', 'draft', 'locked', 'archived', 'deleted'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Title for the new page."},
                        "doc_id": {"type": "string", "description": "Id of the Doc."},
                        "created_by": {"type": "string", "description": "User ID who creates the page."},
                        "parent_page_id": {
                            "type": "string",
                            "description": "Optional parent page id to create a sub-page.",
                        },
                        "body_storage": {"type": "string", "description": "Optional storage-format body content."},
                        "status": {
                            "type": "string",
                            "description": "Optional status (current, draft, locked, archived, deleted). Defaults to current.",
                        },
                    },
                    "required": ["title", "doc_id", "created_by"],
                },
            },
        }
