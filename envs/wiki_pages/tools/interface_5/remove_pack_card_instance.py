import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class RemovePackCardInstance(Tool):
    """Remove a pack card (smart link in confluence) from its host page."""

    @staticmethod
    def invoke(data: Dict[str, Any], pack_card_id: str, deleted_by: str) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(pack_card_id, str) or not pack_card_id.strip():
            return json.dumps({"success": False, "error": "pack_card_id must be provided"})
        if not isinstance(deleted_by, str) or not deleted_by.strip():
            return json.dumps({"success": False, "error": "deleted_by must be provided"})

        smart_links = data.get("smart_links", {})
        users = data.get("users", {})
        if not isinstance(smart_links, dict) or not isinstance(users, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        if deleted_by not in users:
            return json.dumps({"success": False, "error": f"User '{deleted_by}' not found"})

        record = smart_links.get(pack_card_id)
        if not record:
            return json.dumps({"success": False, "error": f"Pack card '{pack_card_id}' not found"})

        removed = smart_links.pop(pack_card_id)
        removed["deleted_by"] = deleted_by
        removed["deleted_at"] = "2025-12-02T12:00:00"
        response = dict(removed)
        identifier = response.pop("smart_link_id", None)
        if identifier:
            response["pack_card_id"] = identifier
        elif "pack_card_id" not in response:
            response["pack_card_id"] = pack_card_id
        return json.dumps({"success": True, "pack_card": response})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "remove_pack_card_instance",
                "description": "Delete a pack card from a host page.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pack_card_id": {"type": "string", "description": "Identifier of the pack card to delete."},
                        "deleted_by": {"type": "string", "description": "User performing the deletion."},
                    },
                    "required": ["pack_card_id", "deleted_by"],
                },
            },
        }
