import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class AddPackCardToTargetTypeInPage(Tool):
    """Create a pack card (similar to smart links in confluence) hosted on a page."""

    @staticmethod
    def invoke(data: Dict[str, Any], fields: Dict[str, Any]) -> str:
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        if not isinstance(fields, dict):
            return json.dumps({"success": False, "error": "fields must be an object"})

        required = ["title", "url", "host_page_id", "created_by"]
        for key in required:
            value = fields.get(key)
            if not isinstance(value, str) or not value.strip():
                return json.dumps({"success": False, "error": f"{key} must be a non-empty string"})

        title = fields["title"].strip()
        url = fields["url"].strip()
        host_page_id = fields["host_page_id"]
        created_by = fields["created_by"]
        target_id = fields.get("target_id")
        client_target_type = fields.get("target_type")

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
            "external": "external",
            "attachment": "attachment",
        }

        pages = data.setdefault("pages", {})
        databases = data.setdefault("databases", {})
        whiteboards = data.setdefault("whiteboards", {})
        smart_links = data.setdefault("smart_links", {})
        users = data.setdefault("users", {})

        if not all(isinstance(obj, dict) for obj in (pages, databases, whiteboards, smart_links, users)):
            return json.dumps({"success": False, "error": "Corrupted storage format"})

        if host_page_id not in pages:
            return json.dumps({"success": False, "error": f"Host page '{host_page_id}' not found"})
        if created_by not in users:
            return json.dumps({"success": False, "error": f"User '{created_by}' not found"})

        internal_target_type = None
        if client_target_type:
            if client_target_type not in type_map:
                return json.dumps(
                    {
                        "success": False,
                        "error": "target_type must be one of page, table, whiteboard, external, attachment",
                    }
                )
            internal_target_type = type_map[client_target_type]
            if internal_target_type != "external" and not target_id:
                return json.dumps({"success": False, "error": "target_id required for non-external types"})
            if target_id:
                lookup_tables = {
                    "page": pages,
                    "database": databases,
                    "whiteboard": whiteboards,
                    "attachment": data.get("attachments", {}),
                }
                table = lookup_tables.get(internal_target_type or client_target_type)
                if table is None or target_id not in table:
                    human_type = "table" if client_target_type == "table" else client_target_type
                    return json.dumps({"success": False, "error": f"target_id '{target_id}' not valid for {human_type}"})
        elif target_id:
            return json.dumps({"success": False, "error": "target_type required when target_id supplied"})

        smart_link_id = next_id(smart_links)
        timestamp = "2025-12-02T12:00:00"
        record = {
            "pack_card_id": smart_link_id,
            "title": title,
            "url": url,
            "target_id": target_id,
            "target_type": internal_target_type,
            "host_page_id": host_page_id,
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp,
        }
        smart_links[smart_link_id] = record

        response_record = dict(record)
        response_record["pack_card_id"] = response_record.pop("smart_link_id", smart_link_id)
        if response_record.get("target_type"):
            reverse_map = {v: k for k, v in type_map.items()}
            response_record["target_type"] = reverse_map.get(response_record["target_type"], response_record["target_type"])

        return json.dumps({"success": True, "pack_card": response_record})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "add_pack_card_to_target_type_in_page",
                "description": "Create a pack card with url hosted on a page.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "Display title for the pack card."},
                                "url": {"type": "string", "description": "Destination URL for the card."},
                                "target_id": {"type": "string", "description": "Optional linked entity identifier."},
                                "target_type": {
                                    "type": "string",
                                    "description": "One of page, table, whiteboard, external, attachment.",
                                },
                                "host_page_id": {"type": "string", "description": "Page hosting the card."},
                                "created_by": {"type": "string", "description": "User creating the card."},
                            },
                            "required": ["title", "url", "host_page_id", "created_by"],
                        }
                    },
                    "required": ["fields"],
                },
            },
        }
