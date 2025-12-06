import json
from typing import Any, Dict, List
from tau_bench.envs.tool import Tool

class AttainDocumentParentHierarchy(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        document_id: str,
        include_self: bool = False,
    ) -> str:
        """
        Attain all ancestor documents of a given document.
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

        results: List[Dict[str, Any]] = []
        visited = set()

        if include_self:
            current_page = pages[document_id]
            doc_record = {
                "document_id": current_page.get("page_id", document_id),
                "title": current_page.get("title"),
                "workspace_id": current_page.get("space_id"),
                "parent_document_id": current_page.get("parent_page_id"),
                "body_storage": current_page.get("body_storage"),
                "status": current_page.get("status"),
                "created_by": current_page.get("created_by"),
                "created_at": current_page.get("created_at"),
                "updated_by": current_page.get("updated_by"),
                "updated_at": current_page.get("updated_at"),
            }
            results.append(doc_record)
            visited.add(document_id)

        # Traverse up the hierarchy
        current_id = pages[document_id].get("parent_page_id")

        while current_id is not None and current_id not in visited:
            current_id = str(current_id)

            if current_id not in pages:
                break

            visited.add(current_id)
            ancestor = pages[current_id]
            
            # Map to Fibery naming
            doc_record = {
                "document_id": ancestor.get("page_id", current_id),
                "title": ancestor.get("title"),
                "workspace_id": ancestor.get("space_id"),
                "parent_document_id": ancestor.get("parent_page_id"),
                "body_storage": ancestor.get("body_storage"),
                "status": ancestor.get("status"),
                "created_by": ancestor.get("created_by"),
                "created_at": ancestor.get("created_at"),
                "updated_by": ancestor.get("updated_by"),
                "updated_at": ancestor.get("updated_at"),
            }
            results.append(doc_record)

            current_id = pages[current_id].get("parent_page_id")

        return json.dumps({
            "entity_type": "documents",
            "document_id": document_id,
            "count": len(results),
            "results": results,
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "attain_document_parent_hierarchy",
                "description": (
                    "Attains all ancestor documents of a given document, traversing up the hierarchy "
                    "from the specified document to the root. "
                    "Results are ordered from the immediate parent to the root."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": (
                                "The ID of the document to get ancestors for (required)."
                            ),
                        },
                        "include_self": {
                            "type": "boolean",
                            "description": (
                                "Whether to include the specified document in the results (True/False). "
                                "Defaults to False."
                            ),
                        },
                    },
                    "required": ["document_id"],
                },
            },
        }

