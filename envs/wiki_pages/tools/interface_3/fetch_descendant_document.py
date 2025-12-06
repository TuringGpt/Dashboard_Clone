import json
from typing import Any, Dict, List
from tau_bench.envs.tool import Tool


class FetchDescendantDocument(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        document_id: str,
        include_root: bool = False,
    ) -> str:
        """
        Fetch all descendant documents of a given document.
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

        def get_descendants(parent_id: str, all_pages: Dict[str, Any]) -> List[Dict[str, Any]]:
            descendants = []
            for pid, page in all_pages.items():
                if page.get("parent_page_id") == parent_id:
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
                    descendants.append(doc_record)
                    # Recursively get descendants of this document
                    descendants.extend(get_descendants(str(pid), all_pages))
            return descendants

        results = []

        if include_root:
            root_page = pages[document_id]
            root_record = {
                "document_id": root_page.get("page_id", document_id),
                "title": root_page.get("title"),
                "workspace_id": root_page.get("space_id"),
                "parent_document_id": root_page.get("parent_page_id"),
                "body_storage": root_page.get("body_storage"),
                "status": root_page.get("status"),
                "created_by": root_page.get("created_by"),
                "created_at": root_page.get("created_at"),
                "updated_by": root_page.get("updated_by"),
                "updated_at": root_page.get("updated_at"),
            }
            results.append(root_record)

        results.extend(get_descendants(document_id, pages))

        return json.dumps({
            "entity_type": "documents",
            "root_document_id": document_id,
            "count": len(results),
            "results": results,
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "fetch_descendant_document",
                "description": (
                    "Fetches all descendant documents (children, grandchildren, etc.) of a given document. "
                    "This performs a recursive traversal of the document hierarchy starting from the specified document."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": (
                                "The ID of the root document to get descendants for (required)."
                            ),
                        },
                        "include_root": {
                            "type": "boolean",
                            "description": (
                                "Whether to include the root document in the results (True/False). "
                                "Defaults to False."
                            ),
                        },
                    },
                    "required": ["document_id"],
                },
            },
        }

