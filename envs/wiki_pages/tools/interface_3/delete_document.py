import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteDocument(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        document_id: str,
        options: Dict[str, Any],
    ) -> str:
        """
        Ejects (soft or hard deletes) a document record.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not document_id:
            return json.dumps({"error": "Missing required parameter: document_id is required"})

        if not options or not isinstance(options, dict):
            return json.dumps({"error": "Missing required parameter: options must be a JSON object"})

        updated_by = options.get("updated_by")
        hard_delete = options.get("hard_delete", False)

        if not updated_by:
            return json.dumps({"error": "Missing required parameter: options.updated_by is required"})

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

        if hard_delete:
            # Check if document has children
            for pid, p in pages.items():
                if p.get("parent_page_id") == document_id:
                    return json.dumps({
                        "error": f"Cannot hard delete document with ID '{document_id}' because it has child documents. "
                        "Delete or reassign child documents first."
                    })

            # Remove from data
            deleted_page = pages.pop(document_id)
            
            # Return with Fibery naming
            output_document = {
                "document_id": deleted_page.get("page_id", document_id),
                "title": deleted_page.get("title"),
                "workspace_id": deleted_page.get("space_id"),
                "parent_document_id": deleted_page.get("parent_page_id"),
                "body_storage": deleted_page.get("body_storage"),
                "status": deleted_page.get("status"),
                "created_by": deleted_page.get("created_by"),
                "created_at": deleted_page.get("created_at"),
                "updated_by": deleted_page.get("updated_by"),
                "updated_at": deleted_page.get("updated_at"),
                "_deleted": True,
            }
            return json.dumps(output_document)
        else:
            # Soft delete - set status to 'deleted'
            page["status"] = "deleted"
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
                "name": "delete_document",
                "description": (
                    """Deletes a document from the wiki.
By default, performs a soft delete by marking the document status as 'deleted' (document remains in system, hidden from view).
Use hard_delete=True to permanently remove the document from the system (cannot be undone).
Hard deletion requires that the document has NO child documents - reassign or delete children first.
Use soft delete for reversible removals; use hard delete for permanent purging.
Deleting a document with children will fail unless child documents are reassigned to a parent or deleted first."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": (
                                "The ID of the document to eject (required)."
                            ),
                        },
                        "options": {
                            "type": "object",
                            "description": (
                                "Options for the delete operation (required). "
                                "Must include 'updated_by'. Optional: 'hard_delete'."
                            ),
                            "properties": {
                                "updated_by": {
                                    "type": "string",
                                    "description": "The user ID of the person performing the deletion (required).",
                                },
                                "hard_delete": {
                                    "type": "boolean",
                                    "description": "Whether to permanently delete the document (True/False). Defaults to False (soft delete). Hard delete will fail if the document has child documents.",
                                },
                            },
                            "required": ["updated_by"],
                        },
                    },
                    "required": ["document_id", "options"],
                },
            },
        }
