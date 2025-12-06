import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class EditAttachmentMetadata(Tool):
    """Update attachment properties like name, URL, or lifecycle status."""

    @staticmethod
    def invoke(data: Dict[str, Any], fields: Dict[str, Any]) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(fields, dict):
            return json.dumps({"success": False, "error": "fields must be an object"})

        attachment_id = fields.get("attachment_id")
        if not isinstance(attachment_id, str) or not attachment_id.strip():
            return json.dumps({"success": False, "error": "attachment_id must be provided"})

        attachments = data.get("attachments", {})
        if not isinstance(attachments, dict):
            return json.dumps({"success": False, "error": "Corrupted attachments store"})

        record = attachments.get(attachment_id)
        if not record:
            return json.dumps({"success": False, "error": f"Attachment '{attachment_id}' not found"})

        allowed_status = {"current", "archived", "deleted"}
        file_name = fields.get("file_name")
        file_url = fields.get("file_url")
        status = fields.get("status")

        if status and status not in allowed_status:
            return json.dumps({"success": False, "error": "Invalid status value"})

        timestamp = "2025-12-02T12:00:00"
        changed = False

        if file_name is not None:
            if not isinstance(file_name, str) or not file_name.strip():
                return json.dumps({"success": False, "error": "file_name must be a non-empty string"})
            record["file_name"] = file_name.strip()
            changed = True

        if file_url is not None:
            if not isinstance(file_url, str) or not file_url.strip():
                return json.dumps({"success": False, "error": "file_url must be a non-empty string"})
            record["file_url"] = file_url.strip()
            changed = True

        if status is not None:
            record["status"] = status
            changed = True

        if not changed:
            return json.dumps({"success": False, "error": "No changes supplied"})

        record["updated_at"] = timestamp
        return json.dumps({"success": True, "attachment": record})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "edit_attachment_metadata",
                "description": "Update attachment metadata such as file name, URL, or status.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "description": "Attachment update payload.",
                            "properties": {
                                "attachment_id": {"type": "string", "description": "Identifier of the attachment."},
                                "file_name": {"type": "string", "description": "New attachment display name."},
                                "file_url": {"type": "string", "description": "New attachment URL."},
                                "status": {
                                    "type": "string",
                                    "description": "Optional status (current, archived, deleted).",
                                },
                            },
                            "required": ["attachment_id"],
                        }
                    },
                    "required": ["fields"],
                },
            },
        }
