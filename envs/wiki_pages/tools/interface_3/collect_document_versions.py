import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class CollectDocumentVersions(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Collect document version (paragraph block) records with optional filters.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if filters is not None and not isinstance(filters, dict):
            return json.dumps({"error": "filters must be a JSON object if provided"})

        # Access Confluence DB table (page_versions)
        table = data.get("page_versions", {})
        results = []
        effective_filters = filters or {}

        # Map Fibery param names to Confluence DB field names
        filter_mapping = {
            "paragraph_block_id": "page_version_id",
            "document_id": "page_id",
        }

        # Convert filter keys from Fibery to Confluence naming
        mapped_filters = {}
        for key, value in effective_filters.items():
            mapped_key = filter_mapping.get(key, key)
            mapped_filters[mapped_key] = value

        # Convert ID values in filters to strings for consistent comparison
        if mapped_filters:
            id_filter_fields = ["page_version_id", "page_id"]
            for field in id_filter_fields:
                if field in mapped_filters and mapped_filters[field] is not None:
                    mapped_filters[field] = str(mapped_filters[field])

        for record_id, record in table.items():
            if not isinstance(record, dict):
                continue

            match = True
            for key, value in mapped_filters.items():
                if key == "page_version_id":
                    stored_id = record.get("page_version_id")
                    if str(record_id) != str(value) and str(stored_id) != str(value):
                        match = False
                        break
                elif key == "version_number":
                    # Handle version_number as integer comparison
                    record_version = record.get("version_number")
                    if record_version != value and str(record_version) != str(value):
                        match = False
                        break
                else:
                    if record.get(key) != value:
                        match = False
                        break

            if match:
                # Map to Fibery naming
                result_record = {
                    "paragraph_block_id": record.get("page_version_id", str(record_id)),
                    "document_id": record.get("page_id"),
                    "version_number": record.get("version_number"),
                    "title": record.get("title"),
                    "body_storage": record.get("body_storage"),
                    "created_at": record.get("created_at"),
                }
                results.append(result_record)

        # Sort by version_number descending (most recent first)
        results.sort(key=lambda x: x.get("version_number", 0), reverse=True)

        return json.dumps({
            "entity_type": "paragraph_blocks",
            "count": len(results),
            "results": results,
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "collect_document_versions",
                "description": (
                    "Retrieves document version history records. "
                    "Each version captures a snapshot of document state including title and content body at that point in time. "
                    "Results are automatically sorted by version number in descending order (most recent version first). "
                    "Use this tool to audit document changes, restore previous content, compare versions, or track editing history."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "object",
                            "description": (
                                "Optional JSON object with filter key-value pairs (AND logic). "
                                "Supported fields: paragraph_block_id, document_id, version_number, title."
                            ),
                            "properties": {
                                "paragraph_block_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the paragraph block/version record to retrieve (e.g., '1', '100').",
                                },
                                "document_id": {
                                    "type": "string",
                                    "description": "The ID of the document to retrieve all versions for (e.g., '5'). Returns version history for that document.",
                                },
                                "version_number": {
                                    "type": "integer",
                                    "description": "The specific version number to retrieve (e.g., 1, 5, 10). Use to get a particular version snapshot.",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "The exact title of the version snapshot to filter by.",
                                },
                            },
                        },
                    },
                    "required": [],
                },
            },
        }

