import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class AlterDocument(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        fields: Dict[str, Any],
    ) -> str:
        """
        Alters an existing document record.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not fields or not isinstance(fields, dict):
            return json.dumps({"error": "Missing required parameter: fields must be a JSON object"})

        document_id = fields.get("document_id")
        updated_by = fields.get("updated_by")
        title = fields.get("title")
        parent_document_id = fields.get("parent_document_id")
        body_storage = fields.get("body_storage")
        status = fields.get("status")

        if not document_id or not updated_by:
            return json.dumps({
                "error": "Missing required parameters: fields.document_id and fields.updated_by are required"
            })

        document_id = str(document_id)
        updated_by = str(updated_by)

        # Access Confluence DB (pages table)
        pages = data.get("pages", {})
        if document_id not in pages:
            return json.dumps({"error": f"Document with ID '{document_id}' not found"})

        # Validate updated_by user exists
        users = data.get("users", {})
        if updated_by not in users:
            return json.dumps({"error": f"User with ID '{updated_by}' not found"})

        page = pages[document_id]

        # Validate status if provided
        if status is not None:
            allowed_statuses = ["current", "draft", "locked", "archived", "deleted"]
            if status not in allowed_statuses:
                return json.dumps({
                    "error": f"Invalid status. Allowed values: {', '.join(allowed_statuses)}"
                })

        # Validate parent_document_id if provided
        if parent_document_id is not None:
            parent_document_id = str(parent_document_id)
            if parent_document_id != "" and parent_document_id not in pages:
                return json.dumps({"error": f"Parent document with ID '{parent_document_id}' not found"})
            # Prevent circular reference
            if parent_document_id == document_id:
                return json.dumps({"error": "A document cannot be its own parent"})

        # Update fields if provided (in Confluence DB format)
        if title is not None:
            page["title"] = title
        if parent_document_id is not None:
            page["parent_page_id"] = parent_document_id if parent_document_id != "" else None
        if body_storage is not None:
            page["body_storage"] = body_storage
        if status is not None:
            page["status"] = status

        # Update metadata
        page["updated_by"] = updated_by
        page["updated_at"] = "2025-12-02T12:00:00"

        # Return with Fibery naming
        output_document = {
            "document_id": page.get("page_id", document_id),
            "title": page.get("title"),
            "workspace_id": page.get("space_id"),
            "parent_document_id": page.get("parent_page_id"),
            "body_storage": page.get("body_storage"),
            "status": page.get("status"),
            "created_by": page.get("created_by"),
            "created_at": page.get("created_at"),
            "updated_by": page.get("updated_by"),
            "updated_at": page.get("updated_at"),
        }

        return json.dumps(output_document)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "alter_document",
                "description": (
                    """Updates an existing document (wiki page).
                    Allows modification of document properties: title, content body, parent document (for hierarchy restructuring), and publication status.
                    Use this tool to edit page content, rename pages, move pages within the hierarchy, or change document status (draft, archived, etc.).
                    Documents form the core content units of wiki workspaces and can be organized hierarchically with parent-child relationships."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "description": (
                                "The fields to update (required). "
                                "Must include 'document_id' and 'updated_by'. "
                                "Optional fields: 'title', 'parent_document_id', 'body_storage', 'status'."
                            ),
                            "properties": {
                                "document_id": {
                                    "type": "string",
                                    "description": "The ID of the document to alter (required).",
                                },
                                "updated_by": {
                                    "type": "string",
                                    "description": "The user ID of the person making the update (required).",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "The new title for the document (optional).",
                                },
                                "parent_document_id": {
                                    "type": "string",
                                    "description": "The new parent document ID (optional). Set to empty string to make it a root document.",
                                },
                                "body_storage": {
                                    "type": "string",
                                    "description": "The new content body for the document (optional).",
                                },
                                "status": {
                                    "type": "string",
                                    "description": "The new status for the document (optional). Allowed values: 'current', 'draft', 'locked', 'archived', 'deleted'.",
                                },
                            },
                            "required": ["document_id", "updated_by"],
                        },
                    },
                    "required": ["fields"],
                },
            },
        }
