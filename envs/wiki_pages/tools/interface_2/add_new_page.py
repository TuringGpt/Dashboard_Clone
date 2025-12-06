import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class AddNewPage(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        title: str,
        site_id: str,
        created_by: str,
        body_storage: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Create a new page in the Confluence database.
        """

        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)

        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data format"})

        pages = data.get("pages", {})
        spaces = data.get("spaces", {})
        users = data.get("users", {})

        # Validate required fields
        if not all([title, site_id, created_by]):
            return json.dumps(
                {
                    "success": False,
                    "error": "Missing required parameters: title, site_id, created_by",
                }
            )

        # Validate site exists
        if site_id not in spaces:
            return json.dumps(
                {"success": False, "error": f"Site with ID '{site_id}' not found"}
            )

        # Validate user exists
        if created_by not in users:
            return json.dumps(
                {"success": False, "error": f"User with ID '{created_by}' not found"}
            )

        # Check for duplicate title in the same site
        for page_data in pages.values():
            if page_data.get("space_id") == site_id and page_data.get("title") == title:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Page with title '{title}' already exists in this site",
                    }
                )

        # Generate new page ID
        new_page_id = generate_id(pages)
        timestamp = "2025-12-02T12:00:00"

        # Create new page record
        new_page = {
            "page_id": new_page_id,
            "title": title,
            "space_id": site_id,
            "parent_page_id": None,
            "body_storage": body_storage,
            "status": status if status else "current",
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp,
        }

        pages[new_page_id] = new_page

        return json.dumps(
            {
                "success": True,
                "page_id": new_page_id,
                "title": title,
                "site_id": site_id,
                "parent_page_id": None,
                "body_storage": body_storage,
                "status": new_page["status"],
                "created_by": created_by,
                "created_at": timestamp,
                "updated_by": created_by,
                "updated_at": timestamp,
            }
        )

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "add_new_page",
                "description": "Create a new page. Requires title, site_id, and created_by. Optional: parent_page_id (for child pages), body_storage (page content), status ('current', 'draft', 'locked', 'archived', 'deleted', defaults to 'current'). Returns created page details including page_id, title, site_id, parent_page_id, body_storage, status, created_by, created_at, updated_by, and updated_at.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Page title (must be unique within the site)",
                        },
                        "site_id": {
                            "type": "string",
                            "description": "Site (space) identifier where the page will be created",
                        },
                        "created_by": {
                            "type": "string",
                            "description": "User ID creating the page",
                        },
                        "body_storage": {
                            "type": "string",
                            "description": "Page content in storage format",
                        },
                        "status": {
                            "type": "string",
                            "description": "Page status: 'current', 'draft', 'locked', 'archived', 'deleted' (defaults to 'current')",
                            "enum": [
                                "current",
                                "draft",
                                "locked",
                                "archived",
                                "deleted",
                            ],
                        },
                    },
                    "required": ["title", "site_id", "created_by"],
                },
            },
        }
