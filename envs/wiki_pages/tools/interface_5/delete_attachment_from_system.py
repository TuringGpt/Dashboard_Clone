import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteAttachmentFromSystem(Tool):
    """Delete an attachment entry after verifying the user initiating the deletion in Conda Workspace."""

    @staticmethod
    def invoke(data: Dict[str, Any], fields: Dict[str, Any]) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(fields, dict):
            return json.dumps({"success": False, "error": "fields must be an object"})

        attachment_id = fields.get("attachment_id")
        deleted_by = fields.get("deleted_by")
        if not isinstance(attachment_id, str) or not attachment_id.strip():
            return json.dumps({"success": False, "error": "attachment_id must be provided"})
        if not isinstance(deleted_by, str) or not deleted_by.strip():
            return json.dumps({"success": False, "error": "deleted_by must be provided"})

        attachments = data.get("attachments", {})
        users = data.get("users", {})
        if not isinstance(attachments, dict) or not isinstance(users, dict):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        if deleted_by not in users:
            return json.dumps({"success": False, "error": f"User '{deleted_by}' not found"})

        record = attachments.get(attachment_id)
        if not record:
            return json.dumps({"success": False, "error": f"Attachment '{attachment_id}' not found"})

        removed = attachments.pop(attachment_id)
        removed["deleted_by"] = deleted_by
        removed["deleted_at"] = "2025-12-02T12:00:00"
        return json.dumps({"success": True, "attachment": removed})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_attachment_from_system",
                "description": "Delete an attachment record from a page/table/whiteboard/pack card.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "properties": {
                                "attachment_id": {"type": "string", "description": "Attachment identifier."},
                                "deleted_by": {"type": "string", "description": "User initiating the deletion."},
                            },
                            "required": ["attachment_id", "deleted_by"],
                        }
                    },
                    "required": ["fields"],
                },
            },
        }
