import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class AddAttachmentEntity(Tool):
    """Upload an attachment to a page, table, whiteboard, or pack card."""

    @staticmethod
    def invoke(data: Dict[str, Any], fields: Dict[str, Any]) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(fields, dict):
            return json.dumps({"success": False, "error": "fields must be an object"})

        required = ["content_id", "content_type", "file_name", "file_url", "uploaded_by"]
        for key in required:
            value = fields.get(key)
            if not isinstance(value, str) or not value.strip():
                return json.dumps({"success": False, "error": f"{key} must be a non-empty string"})

        content_id = fields["content_id"]
        input_type = fields["content_type"]
        status = fields.get("status") or "current"
        file_name = fields["file_name"]
        file_url = fields["file_url"]
        uploaded_by = fields["uploaded_by"]
        host_page_id = fields.get("host_page_id")

        def next_id(table: Dict[str, Any]) -> str:
            numeric = []
            for key in table.keys():
                try:
                    numeric.append(int(key))
                except (TypeError, ValueError):
                    continue
            return str(max(numeric, default=0) + 1)

        type_map = {
            "page": "page",
            "table": "database",
            "whiteboard": "whiteboard",
            "pack_card": "smart_link",
        }
        allowed_status = {"current", "archived", "deleted"}

        attachments = data.setdefault("attachments", {})
        pages = data.setdefault("pages", {})
        databases = data.setdefault("databases", {})
        whiteboards = data.setdefault("whiteboards", {})
        smart_links = data.setdefault("smart_links", {})
        users = data.setdefault("users", {})
        stores = {
            "page": pages,
            "database": databases,
            "whiteboard": whiteboards,
            "smart_link": smart_links,
        }

        if not all(isinstance(obj, dict) for obj in (attachments, pages, databases, whiteboards, smart_links, users)):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        mapped_type = type_map.get(input_type)
        if not mapped_type:
            return json.dumps({"success": False, "error": f"Unsupported content_type '{input_type}'"})
        if status not in allowed_status:
            return json.dumps({"success": False, "error": "status must be one of current/archived/deleted"})
        if uploaded_by not in users:
            return json.dumps({"success": False, "error": f"User '{uploaded_by}' not found"})
        if host_page_id and host_page_id not in pages:
            return json.dumps({"success": False, "error": f"Host page '{host_page_id}' not found"})

        target_store = stores[mapped_type]
        if content_id not in target_store:
            human_name = {"database": "table", "smart_link": "pack_card"}.get(mapped_type, mapped_type)
            return json.dumps({"success": False, "error": f"{human_name} '{content_id}' not found"})

        attachment_id = next_id(attachments)
        timestamp = "2025-12-02T12:00:00"
        record = {
            "attachment_id": attachment_id,
            "content_id": content_id,
            "content_type": mapped_type,
            "host_page_id": host_page_id,
            "file_name": file_name,
            "file_url": file_url,
            "status": status,
            "uploaded_by": uploaded_by,
            "uploaded_at": timestamp,
            "updated_at": timestamp,
        }
        attachments[attachment_id] = record

        response = dict(record)
        response["content_type"] = input_type
        return json.dumps({"success": True, "attachment": response})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "add_attachment_entity",
                "description": "Upload an attachment against a page, table, whiteboard, or pack card.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "description": "Attachment metadata describing destination and file.",
                            "properties": {
                                "content_id": {"type": "string", "description": "Target entity identifier."},
                                "content_type": {
                                    "type": "string",
                                    "description": "Allowed values: page, table, whiteboard, pack_card.",
                                },
                                "host_page_id": {
                                    "type": "string",
                                    "description": "Optional page hosting the attachment (if applicable).",
                                },
                                "file_name": {"type": "string", "description": "Display name of the file."},
                                "file_url": {"type": "string", "description": "URL pointing to the stored file."},
                                "status": {
                                    "type": "string",
                                    "description": "Attachment status (current, archived, deleted). Defaults to current.",
                                },
                                "uploaded_by": {"type": "string", "description": "User uploading the attachment."},
                            },
                            "required": ["content_id", "content_type", "file_name", "file_url", "uploaded_by"],
                        }
                    },
                    "required": ["fields"],
                },
            },
        }
