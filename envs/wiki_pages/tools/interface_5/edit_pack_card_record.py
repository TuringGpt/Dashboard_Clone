import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class EditPackCardRecord(Tool):
    """Update metadata for a pack card (smart link in confluence) hosted on a page."""

    @staticmethod
    def invoke(
        data: Dict[str, Any],
        pack_card_id: str,
        title: Optional[str] = None,
        url: Optional[str] = None,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(pack_card_id, str) or not pack_card_id.strip():
            return json.dumps({"success": False, "error": "pack_card_id must be provided"})

        smart_links = data.get("smart_links", {})
        pages = data.get("pages", {})
        databases = data.get("databases", {})
        whiteboards = data.get("whiteboards", {})
        attachments = data.get("attachments", {})
        users = data.get("users", {})
        if not all(isinstance(obj, dict) for obj in (smart_links, pages, databases, whiteboards, attachments, users)):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        record = smart_links.get(pack_card_id)
        if not record:
            return json.dumps({"success": False, "error": f"Pack card '{pack_card_id}' not found"})

        if updated_by:
            if updated_by not in users:
                return json.dumps({"success": False, "error": f"User '{updated_by}' not found"})

        if title is None and url is None and target_id is None and target_type is None:
            return json.dumps({"success": False, "error": "No fields provided to update"})

        if title is not None:
            if not isinstance(title, str) or not title.strip():
                return json.dumps({"success": False, "error": "title must be a non-empty string"})
            record["title"] = title.strip()

        if url is not None:
            if not isinstance(url, str) or not url.strip():
                return json.dumps({"success": False, "error": "url must be a non-empty string"})
            record["url"] = url.strip()

        type_map = {
            "page": "page",
            "table": "database",
            "whiteboard": "whiteboard",
            "external": "external",
            "attachment": "attachment",
        }

        if target_id is not None or target_type is not None:
            client_target_type = target_type or record.get("target_type")
            if client_target_type and client_target_type not in type_map:
                return json.dumps({"success": False, "error": "Invalid target_type"})
            internal_type = type_map.get(client_target_type, record.get("target_type"))
            if client_target_type and client_target_type != "external":
                if not target_id and not record.get("target_id"):
                    return json.dumps({"success": False, "error": "target_id required for non-external types"})
                candidate_id = target_id or record.get("target_id")
                lookup = {
                    "page": pages,
                    "database": databases,
                    "whiteboard": whiteboards,
                    "attachment": attachments,
                }.get(internal_type)
                if lookup is None or candidate_id not in lookup:
                    human = "table" if client_target_type == "table" else client_target_type
                    return json.dumps({"success": False, "error": f"target_id '{candidate_id}' not valid for {human}"})
            record["target_type"] = internal_type
            if client_target_type == "external":
                record["target_id"] = target_id
            elif target_id is not None:
                record["target_id"] = target_id

        if updated_by:
            record["updated_by"] = updated_by
        record["updated_at"] = "2025-12-02T12:00:00"

        response_record = dict(record)
        pack_card_identifier = response_record.pop("smart_link_id", None)
        if pack_card_identifier:
            response_record["pack_card_id"] = pack_card_identifier
        elif "pack_card_id" not in response_record:
            response_record["pack_card_id"] = pack_card_id
        reverse_map = {v: k for k, v in type_map.items()}
        if response_record.get("target_type"):
            response_record["target_type"] = reverse_map.get(response_record["target_type"], response_record["target_type"])

        return json.dumps({"success": True, "pack_card": response_record})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "edit_pack_card_record",
                "description": "Update pack card metadata including title, URL, or linked target.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pack_card_id": {"type": "string", "description": "Identifier of the pack card to update."},
                        "title": {"type": "string", "description": "New title (optional)."},
                        "url": {"type": "string", "description": "New URL (optional)."},
                        "target_id": {"type": "string", "description": "New linked entity identifier (optional)."},
                        "target_type": {
                            "type": "string",
                            "description": "One of page, table, whiteboard, external, attachment.",
                        },
                        "updated_by": {"type": "string", "description": "User applying the change."},
                    },
                    "required": ["pack_card_id", "updated_by"],
                },
            },
        }
