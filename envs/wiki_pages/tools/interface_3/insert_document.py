import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class InsertDocument(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        title: str,
        workspace_id: str,
        created_by: str,
        parent_document_id: Optional[str] = None,
        body_storage: Optional[str] = None,
        status: str = "current",
    ) -> str:
        """
        Create a new document in the Fibery workspace.
        Maps to Confluence pages table.
        
        Returns only Fibery terminology in output - no internal Confluence DB fields exposed.
        """

        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)

        timestamp = "2025-12-02T12:00:00"
        pages = data.get("pages", {})
        spaces = data.get("spaces", {})
        users = data.get("users", {})

        # Validate workspace (space) exists
        if workspace_id not in spaces:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Workspace with ID '{workspace_id}' not found",
                }
            )

        # Validate user exists and is active
        if created_by not in users:
            return json.dumps(
                {"success": False, "error": f"User with ID '{created_by}' not found"}
            )

        user = users[created_by]
        if user.get("status") != "active":
            return json.dumps(
                {
                    "success": False,
                    "error": f"User with ID '{created_by}' is not active",
                }
            )

        # Validate parent document if provided
        if parent_document_id:
            if parent_document_id not in pages:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Parent document with ID '{parent_document_id}' not found",
                    }
                )

            parent_page = pages[parent_document_id]
            if parent_page.get("space_id") != workspace_id:
                return json.dumps(
                    {
                        "success": False,
                        "error": "Parent document must be in the same workspace",
                    }
                )

        # Validate status
        valid_statuses = ["current", "draft", "locked", "archived", "deleted"]
        if status not in valid_statuses:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                }
            )

        # Check for duplicate title in same hierarchy level
        for existing_page in pages.values():
            if (
                existing_page.get("title") == title
                and existing_page.get("space_id") == workspace_id
                and existing_page.get("parent_page_id") == parent_document_id
            ):
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Document with title '{title}' already exists at this hierarchy level",
                    }
                )

        # Generate new document ID
        new_page_id = generate_id(pages)

        # Create new document (page) - stored in Confluence DB format internally
        new_page = {
            "page_id": new_page_id,
            "title": title,
            "space_id": workspace_id,
            "parent_page_id": parent_document_id,
            "body_storage": body_storage,
            "status": status,
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp,
        }

        pages[new_page_id] = new_page

        # Return with ONLY Fibery terminology - no internal Confluence DB fields exposed
        return json.dumps(
            {
                "success": True,
                "document_id": new_page_id,
                "document": {
                    "document_id": new_page_id,
                    "title": title,
                    "workspace_id": workspace_id,
                    "parent_document_id": parent_document_id,
                    "body_storage": body_storage,
                    "status": status,
                    "created_by": created_by,
                    "created_at": timestamp,
                    "updated_by": created_by,
                    "updated_at": timestamp,
                }
            }
        )

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "insert_document",
                "description": (
                    "Create a new document in a workspace. "
                    "Documents are hierarchical and can have parent-child relationships. "
                    "The workspace must exist, and the creator must be an active user. "
                    "If a parent document is specified, it must exist in the same workspace. "
                    "Duplicate titles are not allowed at the same hierarchy level."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": (
                                "Title of the document. "
                                "Must be unique at the same hierarchy level within the workspace."
                            ),
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": (
                                "ID of the workspace where the document will be created. "
                                "The workspace must exist."
                            ),
                        },
                        "created_by": {
                            "type": "string",
                            "description": (
                                "User ID of the document creator. "
                                "The user must exist and be active."
                            ),
                        },
                        "parent_document_id": {
                            "type": "string",
                            "description": (
                                "ID of the parent document for creating nested/child documents. "
                                "If provided, the parent must exist in the same workspace."
                            ),
                        },
                        "body_storage": {
                            "type": "string",
                            "description": "Content/body of the document.",
                        },
                        "status": {
                            "type": "string",
                            "description": "Document status. Defaults to 'current'.",
                            "enum": [
                                "current",
                                "draft",
                                "locked",
                                "archived",
                                "deleted",
                            ],
                        },
                    },
                    "required": ["title", "workspace_id", "created_by"],
                },
            },
        }