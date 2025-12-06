import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class DiscoverDirectChildren(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        document_id: str,
        status: Optional[str] = None,
    ) -> str:
        """
        Discover direct child documents of a given document.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not document_id:
            return json.dumps({"error": "Missing required parameter: document_id is required"})

        document_id = str(document_id)

        # Access Confluence DB (pages table)
        pages = data.get("pages", {})
        if document_id not in pages:
            return json.dumps({"error": f"Document with ID '{document_id}' not found"})

        # Validate status if provided
        if status is not None:
            allowed_statuses = ["current", "draft", "locked", "archived", "deleted"]
            if status not in allowed_statuses:
                return json.dumps({
                    "error": f"Invalid status. Allowed values: {', '.join(allowed_statuses)}"
                })

        results = []
        for pid, page in pages.items():
            if page.get("parent_page_id") == document_id:
                # Apply status filter if provided
                if status is not None and page.get("status") != status:
                    continue

                # Map to Fibery naming
                doc_record = {
                    "document_id": page.get("page_id", str(pid)),
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
                results.append(doc_record)

        return json.dumps({
            "entity_type": "documents",
            "parent_document_id": document_id,
            "count": len(results),
            "results": results,
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "discover_direct_children",
                "description": (
                    """Retrieves the immediate child documents of a specified document.
Returns only direct children (one level down in hierarchy), NOT grandchildren or deeper descendants.
Optional status filter allows retrieving only children with specific status (current, draft, archived, deleted).
Use this tool to see the next level of document structure; use fetch_descendant_document to see all descendants.
Useful for rendering document hierarchies, understanding document structure, or managing child documents."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": (
                                "The ID of the parent document to get children for (required)."
                            ),
                        },
                        "status": {
                            "type": "string",
                            "description": (
                                "Filter children by status (optional). "
                                "Allowed values: 'current', 'draft', 'locked', 'archived', 'deleted'."
                            ),
                        },
                    },
                    "required": ["document_id"],
                },
            },
        }

