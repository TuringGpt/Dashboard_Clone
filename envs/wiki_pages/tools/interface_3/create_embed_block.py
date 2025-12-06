import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class CreateEmbedBlock(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        title: str,
        url: str,
        host_document_id: str,
        created_by: str,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
    ) -> str:
        """
        Creates a new embed block (smart link) record.
        """
        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            max_id = 0
            for k in table.keys():
                try:
                    max_id = max(max_id, int(k))
                except ValueError:
                    continue
            return str(max_id + 1)

        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not title or not url or not host_document_id or not created_by:
            return json.dumps({
                "error": "Missing required parameters: title, url, host_document_id, and created_by are required"
            })

        # Convert IDs to strings
        host_document_id = str(host_document_id)
        created_by = str(created_by)
        if target_id is not None:
            target_id = str(target_id)

        # Validate target_type if provided
        if target_type is not None:
            allowed_target_types = ["document", "type", "whiteboard_view", "external", "file_block"]
            if target_type not in allowed_target_types:
                return json.dumps({
                    "error": f"Invalid target_type. Allowed values: {', '.join(allowed_target_types)}"
                })

        # Validate host_document_id exists (access Confluence DB - pages table)
        pages = data.get("pages", {})
        if host_document_id not in pages:
            return json.dumps({"error": f"Host document with ID '{host_document_id}' not found"})

        # Validate creator exists
        users = data.get("users", {})
        if created_by not in users:
            return json.dumps({"error": f"User with ID '{created_by}' not found"})

        # Access Confluence DB (smart_links table)
        smart_links = data.setdefault("smart_links", {})

        timestamp = "2025-12-02T12:00:00"
        new_embed_block_id = generate_id(smart_links)

        # Map Fibery target_type to Confluence target_type
        target_type_mapping = {
            "document": "page",
            "type": "database",
            "whiteboard_view": "whiteboard",
            "external": "external",
            "file_block": "attachment",
        }
        db_target_type = target_type_mapping.get(target_type, target_type) if target_type else None

        # Store in Confluence DB format
        new_smart_link_db = {
            "smart_link_id": new_embed_block_id,
            "title": title,
            "url": url,
            "target_id": target_id,
            "target_type": db_target_type,
            "host_page_id": host_document_id,
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp,
        }

        smart_links[new_embed_block_id] = new_smart_link_db

        # Return with Fibery naming
        output_embed_block = {
            "embed_block_id": new_embed_block_id,
            "title": title,
            "url": url,
            "target_id": target_id,
            "target_type": target_type,
            "host_document_id": host_document_id,
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp,
        }

        return json.dumps(output_embed_block)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_embed_block",
                "description": (
                    """Creates a new embedded resource reference (smart link) within a document.
Allows linking to internal wiki content (documents, datatypes, whiteboards) or external URLs from within a wiki page.
Use this tool to create rich references that maintain relationships between content pieces and support navigation.
Embed blocks appear as clickable links or rich previews that help readers navigate between related content.
The embedded resource can target documents, data types, whiteboard views, external websites, or file attachments."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": (
                                "The display title for the embed block (required)."
                            ),
                        },
                        "url": {
                            "type": "string",
                            "description": (
                                "The URL that the embed block points to (required)."
                            ),
                        },
                        "host_document_id": {
                            "type": "string",
                            "description": (
                                "The ID of the document where the embed block is displayed (required)."
                            ),
                        },
                        "created_by": {
                            "type": "string",
                            "description": (
                                "The user ID of the creator (required)."
                            ),
                        },
                        "target_id": {
                            "type": "string",
                            "description": (
                                "The ID of the target entity this embed block references (optional)."
                            ),
                        },
                        "target_type": {
                            "type": "string",
                            "description": (
                                "The type of the target entity (optional). "
                                "Allowed values: 'document', 'type', 'whiteboard_view', 'external', 'file_block'."
                            ),
                        },
                    },
                    "required": ["title", "url", "host_document_id", "created_by"],
                },
            },
        }

