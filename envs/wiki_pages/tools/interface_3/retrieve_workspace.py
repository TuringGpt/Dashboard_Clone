import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool


class RetrieveWorkspace(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Retrieve workspace records with optional filters.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if filters is not None and not isinstance(filters, dict):
            return json.dumps({"error": "filters must be a JSON object if provided"})

        # Access Confluence DB table (spaces)
        table = data.get("spaces", {})
        results = []
        effective_filters = filters or {}

        # Map Fibery param names to Confluence DB field names for filtering
        filter_mapping = {
            "workspace_id": "space_id",
            "workspace_key": "space_key",
        }

        # Convert filter keys from Fibery to Confluence naming
        mapped_filters = {}
        for key, value in effective_filters.items():
            mapped_key = filter_mapping.get(key, key)
            mapped_filters[mapped_key] = value

        # Convert ID values in filters to strings for consistent comparison
        if mapped_filters:
            id_filter_fields = ["space_id", "created_by"]
            for field in id_filter_fields:
                if field in mapped_filters and mapped_filters[field] is not None:
                    mapped_filters[field] = str(mapped_filters[field])

        for record_id, record in table.items():
            if not isinstance(record, dict):
                continue

            match = True
            for key, value in mapped_filters.items():
                if key == "space_id":
                    stored_id = record.get("space_id")
                    if str(record_id) != str(value) and str(stored_id) != str(value):
                        match = False
                        break
                else:
                    if record.get(key) != value:
                        match = False
                        break

            if match:
                result_record = {}
                # Map Confluence output to Fibery naming
                result_record["workspace_id"] = record.get("space_id", str(record_id))
                result_record["workspace_key"] = record.get("space_key")
                result_record["name"] = record.get("name")
                result_record["description"] = record.get("description")
                result_record["type"] = record.get("type")
                result_record["status"] = record.get("status")
                result_record["created_by"] = record.get("created_by")
                result_record["created_at"] = record.get("created_at")
                result_record["updated_at"] = record.get("updated_at")
                results.append(result_record)

        return json.dumps({
            "entity_type": "workspaces",
            "count": len(results),
            "results": results,
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "retrieve_workspace",
                "description": (
                    "Retrieves workspace records. "
                    "Workspaces are containers that organize documents, types, whiteboard views, and other content. "
                    "Optional filters allow narrowing results by workspace attributes."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "object",
                            "description": (
                                "Optional JSON object with filter key-value pairs (AND logic). "
                                "Supported fields: workspace_id, workspace_key, name, type, status, created_by. "
                                "type enum: 'global', 'personal'. status enum: 'current', 'archived'."
                            ),
                            "properties": {
                                "workspace_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the workspace to retrieve (e.g., '1', '25').",
                                },
                                "workspace_key": {
                                    "type": "string",
                                    "description": "The unique key identifier of the workspace (e.g., 'SPACE001', 'PROJECT_A').",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "The exact name of the workspace to filter by.",
                                },
                                "type": {
                                    "type": "string",
                                    "description": "The type of workspace. Allowed values: 'global' (shared across organization), 'personal' (individual user workspace).",
                                },
                                "status": {
                                    "type": "string",
                                    "description": "The status of the workspace. Allowed values: 'current' (active workspace), 'archived' (inactive/archived workspace).",
                                },
                                "created_by": {
                                    "type": "string",
                                    "description": "The user_id of the workspace creator (e.g., '5', '42').",
                                },
                            },
                        },
                    },
                    "required": [],
                },
            },
        }

