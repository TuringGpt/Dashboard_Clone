import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool


class AlterEmbedBlock(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        embed_block_id: str,
        updated_by: str,
        title: Optional[str] = None,
        url: Optional[str] = None,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
    ) -> str:
        """
        Alters an existing embed block record.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not embed_block_id or not updated_by:
            return json.dumps({
                "error": "Missing required parameters: embed_block_id and updated_by are required"
            })

        embed_block_id = str(embed_block_id)
        updated_by = str(updated_by)

        # Access Confluence DB (smart_links table)
        smart_links = data.get("smart_links", {})
        if embed_block_id not in smart_links:
            return json.dumps({"error": f"Embed block with ID '{embed_block_id}' not found"})

        # Validate updated_by user exists
        users = data.get("users", {})
        if updated_by not in users:
            return json.dumps({"error": f"User with ID '{updated_by}' not found"})

        smart_link = smart_links[embed_block_id]

        # Validate target_type if provided
        if target_type is not None:
            allowed_target_types = ["document", "type", "whiteboard_view", "external", "file_block"]
            if target_type not in allowed_target_types:
                return json.dumps({
                    "error": f"Invalid target_type. Allowed values: {', '.join(allowed_target_types)}"
                })

        # Update fields if provided
        if title is not None:
            smart_link["title"] = title
        if url is not None:
            smart_link["url"] = url
        if target_id is not None:
            smart_link["target_id"] = str(target_id)
        if target_type is not None:
            # Map Fibery target_type to Confluence target_type
            target_type_mapping = {
                "document": "page",
                "type": "database",
                "whiteboard_view": "whiteboard",
                "external": "external",
                "file_block": "attachment",
            }
            smart_link["target_type"] = target_type_mapping.get(target_type, target_type)

        # Update metadata
        smart_link["updated_by"] = updated_by
        smart_link["updated_at"] = "2025-12-02T12:00:00"

        # Map Confluence target_type back to Fibery target_type for output
        reverse_target_type_mapping = {
            "page": "document",
            "database": "type",
            "whiteboard": "whiteboard_view",
            "external": "external",
            "attachment": "file_block",
        }
        fibery_target_type = reverse_target_type_mapping.get(
            smart_link.get("target_type"), 
            smart_link.get("target_type")
        )

        # Return with Fibery naming
        output_embed_block = {
            "embed_block_id": smart_link.get("smart_link_id", embed_block_id),
            "title": smart_link.get("title"),
            "url": smart_link.get("url"),
            "target_id": smart_link.get("target_id"),
            "target_type": fibery_target_type,
            "host_document_id": smart_link.get("host_page_id"),
            "created_by": smart_link.get("created_by"),
            "created_at": smart_link.get("created_at"),
            "updated_by": smart_link.get("updated_by"),
            "updated_at": smart_link.get("updated_at"),
        }

        return json.dumps(output_embed_block)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "alter_embed_block",
                "description": (
                    """Updates an existing embedded resource reference (smart link).
Allows modification of embed block properties: display title, external URL, and target reference (internal content or external link).
Use this tool when you need to change how an embedded resource appears or what it references.
Embed blocks allow wiki pages to reference and display other documents, data types, whiteboard views, or external URLs."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "embed_block_id": {
                            "type": "string",
                            "description": (
                                "The ID of the embed block to alter (required)."
                            ),
                        },
                        "updated_by": {
                            "type": "string",
                            "description": (
                                "The user ID of the person making the update (required)."
                            ),
                        },
                        "title": {
                            "type": "string",
                            "description": (
                                "The new title for the embed block (optional)."
                            ),
                        },
                        "url": {
                            "type": "string",
                            "description": (
                                "The new URL for the embed block (optional)."
                            ),
                        },
                        "target_id": {
                            "type": "string",
                            "description": (
                                "The new target entity ID (optional)."
                            ),
                        },
                        "target_type": {
                            "type": "string",
                            "description": (
                                "The new target type (optional). "
                                "Allowed values: 'document', 'type', 'whiteboard_view', 'external', 'file_block'."
                            ),
                        },
                    },
                    "required": ["embed_block_id", "updated_by"],
                },
            },
        }
