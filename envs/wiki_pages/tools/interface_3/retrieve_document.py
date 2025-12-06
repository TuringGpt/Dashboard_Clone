import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class RetrieveDocument(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Retrieve document records with optional filters.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if filters is not None and not isinstance(filters, dict):
            return json.dumps({"error": "filters must be a JSON object if provided"})

        # Access Confluence DB table (pages)
        table = data.get("pages", {})
        results = []
        effective_filters = filters or {}

        # Map Fibery param names to Confluence DB field names
        filter_mapping = {
            "document_id": "page_id",
            "workspace_id": "space_id",
            "parent_document_id": "parent_page_id",
        }

        # Convert filter keys from Fibery to Confluence naming
        mapped_filters = {}
        for key, value in effective_filters.items():
            mapped_key = filter_mapping.get(key, key)
            mapped_filters[mapped_key] = value

        # Convert ID values in filters to strings for consistent comparison
        if mapped_filters:
            id_filter_fields = ["page_id", "space_id", "parent_page_id", "created_by", "updated_by"]
            for field in id_filter_fields:
                if field in mapped_filters and mapped_filters[field] is not None:
                    mapped_filters[field] = str(mapped_filters[field])

        for record_id, record in table.items():
            if not isinstance(record, dict):
                continue

            match = True
            for key, value in mapped_filters.items():
                if key == "page_id":
                    stored_id = record.get("page_id")
                    if str(record_id) != str(value) and str(stored_id) != str(value):
                        match = False
                        break
                else:
                    if record.get(key) != value:
                        match = False
                        break

            if match:
                # Map Confluence output to Fibery naming
                result_record = {
                    "document_id": record.get("page_id", str(record_id)),
                    "title": record.get("title"),
                    "workspace_id": record.get("space_id"),
                    "parent_document_id": record.get("parent_page_id"),
                    "body_storage": record.get("body_storage"),
                    "status": record.get("status"),
                    "created_by": record.get("created_by"),
                    "created_at": record.get("created_at"),
                    "updated_by": record.get("updated_by"),
                    "updated_at": record.get("updated_at"),
                }
                results.append(result_record)

        return json.dumps({
            "entity_type": "documents",
            "count": len(results),
            "results": results,
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "retrieve_document",
                "description": (
                    "Retrieves document details. "
                    "Documents are the primary content units that can contain text, embedded content, "
                    "and can be organized hierarchically within workspaces. "
                    "Optional filters allow narrowing results by document attributes."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "object",
                            "description": (
                                "Optional JSON object with filter key-value pairs (AND logic). "
                                "Supported fields: document_id, title, workspace_id, parent_document_id, status, created_by, updated_by. "
                                "status enum: 'current', 'draft', 'locked', 'archived', 'deleted'."
                            ),
                            "properties": {
                                "document_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the document to retrieve (e.g., '1', '50').",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "The exact title of the document to filter by.",
                                },
                                "workspace_id": {
                                    "type": "string",
                                    "description": "The ID of the workspace containing the document (e.g., '3').",
                                },
                                "parent_document_id": {
                                    "type": "string",
                                    "description": "The ID of the parent document (e.g., '10'). Pass null to filter for root-level documents only.",
                                },
                                "status": {
                                    "type": "string",
                                    "description": "The status of the document. Allowed values: 'current' (active/published), 'draft' (work in progress), 'locked' (cannot be edited), 'archived' (inactive), 'deleted' (soft deleted).",
                                },
                                "created_by": {
                                    "type": "string",
                                    "description": "The user_id of the document creator (e.g., '5').",
                                },
                                "updated_by": {
                                    "type": "string",
                                    "description": "The user_id of the last person who updated the document (e.g., '12').",
                                },
                            },
                        },
                    },
                    "required": [],
                },
            },
        }

