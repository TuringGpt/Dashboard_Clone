import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class FetchEntityInformation(Tool):
    """Retrieve a single entity (pack card, table, whiteboard, label, attachment) by ID and type."""

    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_id: str,
        entity_type: str,
        status: Optional[str] = None,
    ) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(entity_id, str) or not entity_id.strip():
            return json.dumps({"success": False, "error": "entity_id must be provided"})
        entity_map = {
            "pack_card": ("smart_links", "smart_link_id", "pack_card_id"),
            "table": ("databases", "database_id", "table_id"),
            "whiteboard": ("whiteboards", "whiteboard_id", "whiteboard_id"),
            "attachment": ("attachments", "attachment_id", "attachment_id"),
            "label": ("page_labels", "page_label_id", "page_label_id"),
        }

        if entity_type not in entity_map:
            return json.dumps(
                {"success": False, "error": "entity_type must be one of pack_card, table, whiteboard, attachment, label"}
            )

        store_name, storage_key, response_key = entity_map[entity_type]
        table = data.get(store_name, {})
        if not isinstance(table, dict):
            return json.dumps({"success": False, "error": f"Corrupted store for {entity_type}"})

        record = table.get(entity_id)
        if not record:
            return json.dumps({"success": False, "error": f"{entity_type} '{entity_id}' not found"})

        if status:
            record_status = record.get("status")
            if record_status is None:
                return json.dumps({"success": False, "error": f"{entity_type} does not support status filtering"})
            if record_status != status:
                return json.dumps({"success": False, "error": f"{entity_type} '{entity_id}' not in status '{status}'"})

        response = dict(record)
        response[response_key] = response.pop(storage_key, entity_id)

        # Remove storage-specific keys
        if entity_type == "pack_card" and "smart_link_id" in response:
            response.pop("smart_link_id", None)
        if entity_type == "table":
            response.pop("database_id", None)

        return json.dumps({"success": True, "entity": response})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "fetch_entity_information",
                "description": "Retrieve a pack card, table, or whiteboard, label, attachment by id.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "Id of the entity."},
                        "entity_type": {
                            "type": "string",
                            "description": "One of pack_card, table, whiteboard, label, attachment.",
                        },
                        "status": {"type": "string", "description": "Optional status filter (exact match)."},
                    },
                    "required": ["entity_id", "entity_type"],
                },
            },
        }
