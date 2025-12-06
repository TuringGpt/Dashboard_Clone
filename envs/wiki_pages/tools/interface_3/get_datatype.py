import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool


class GetDatatype(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Retrieve type (database) records with optional filters.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if filters is not None and not isinstance(filters, dict):
            return json.dumps({"error": "filters must be a JSON object if provided"})

        # Access Confluence DB table (databases)
        table = data.get("databases", {})
        results = []
        effective_filters = filters or {}

        # Map Fibery param names to Confluence DB field names
        filter_mapping = {
            "type_id": "database_id",
            "host_workspace_id": "host_space_id",
            "host_document_id": "host_page_id",
        }

        # Convert filter keys from Fibery to Confluence naming
        mapped_filters = {}
        for key, value in effective_filters.items():
            mapped_key = filter_mapping.get(key, key)
            mapped_filters[mapped_key] = value

        # Convert ID values in filters to strings for consistent comparison
        if mapped_filters:
            id_filter_fields = ["database_id", "host_space_id", "host_page_id", "created_by", "updated_by"]
            for field in id_filter_fields:
                if field in mapped_filters and mapped_filters[field] is not None:
                    mapped_filters[field] = str(mapped_filters[field])

        for record_id, record in table.items():
            if not isinstance(record, dict):
                continue

            match = True
            for key, value in mapped_filters.items():
                if key == "database_id":
                    stored_id = record.get("database_id")
                    if str(record_id) != str(value) and str(stored_id) != str(value):
                        match = False
                        break
                else:
                    if record.get(key) != value:
                        match = False
                        break

            if match:
                # Map to Fibery naming
                result_record = {
                    "type_id": record.get("database_id", str(record_id)),
                    "title": record.get("title"),
                    "host_workspace_id": record.get("host_space_id"),
                    "host_document_id": record.get("host_page_id"),
                    "description": record.get("description"),
                    "status": record.get("status"),
                    "created_by": record.get("created_by"),
                    "created_at": record.get("created_at"),
                    "updated_by": record.get("updated_by"),
                    "updated_at": record.get("updated_at"),
                }
                results.append(result_record)

        return json.dumps({
            "entity_type": "types",
            "count": len(results),
            "results": results,
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_datatype",
                "description": (
                    "Retrieves datatype (database) definitions from the wiki. "
                    "Datatypes are structured data containers for organizing and managing related information - similar to database tables. "
                    "Can be hosted at workspace level (shared across workspace) or embedded in documents (document-specific). "
                    "Use this tool to inventory datatypes, find specific data structures, or manage datatype definitions. "
                    "Datatypes differ from documents: documents contain narrative content; datatypes organize structured data records."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "object",
                            "description": (
                                "Optional JSON object with filter key-value pairs (AND logic). "
                                "Supported fields: type_id, title, host_workspace_id, host_document_id, status, created_by, updated_by. "
                                "status enum: 'current', 'archived', 'deleted'."
                            ),
                            "properties": {
                                "type_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the datatype to retrieve (e.g., '1', '25').",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "The exact title of the datatype to filter by.",
                                },
                                "host_workspace_id": {
                                    "type": "string",
                                    "description": "The ID of the workspace hosting the datatype (e.g., '3'). Use this to find workspace-level datatypes.",
                                },
                                "host_document_id": {
                                    "type": "string",
                                    "description": "The ID of the document hosting the datatype (e.g., '10'). Use this to find document-embedded datatypes.",
                                },
                                "status": {
                                    "type": "string",
                                    "description": "The status of the datatype. Allowed values: 'current' (active/in use), 'archived' (inactive), 'deleted' (soft deleted).",
                                },
                                "created_by": {
                                    "type": "string",
                                    "description": "The user_id of the datatype creator (e.g., '5').",
                                },
                                "updated_by": {
                                    "type": "string",
                                    "description": "The user_id of the last person who updated the datatype (e.g., '12').",
                                },
                            },
                        },
                    },
                    "required": [],
                },
            },
        }

