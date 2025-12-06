import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class RemoveEmbedBlock(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        embed_block_id: str,
    ) -> str:
        """
        Ejects (permanently deletes) an embed block record.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not embed_block_id:
            return json.dumps({
                "error": "Missing required parameter: embed_block_id is required"
            })

        embed_block_id = str(embed_block_id)

        # Access Confluence DB (smart_links table)
        smart_links = data.get("smart_links", {})
        if embed_block_id not in smart_links:
            return json.dumps({"error": f"Embed block with ID '{embed_block_id}' not found"})

        # Remove from data
        deleted_smart_link = smart_links.pop(embed_block_id)
        
        # Map Confluence target_type to Fibery target_type
        target_type_mapping = {
            "page": "document",
            "database": "type",
            "whiteboard": "whiteboard_view",
            "external": "external",
        }
        fibery_target_type = target_type_mapping.get(
            deleted_smart_link.get("target_type"), 
            deleted_smart_link.get("target_type")
        )

        # Return with Fibery naming
        output_embed_block = {
            "embed_block_id": deleted_smart_link.get("smart_link_id", embed_block_id),
            "title": deleted_smart_link.get("title"),
            "url": deleted_smart_link.get("url"),
            "target_id": deleted_smart_link.get("target_id"),
            "target_type": fibery_target_type,
            "host_document_id": deleted_smart_link.get("host_page_id"),
            "created_by": deleted_smart_link.get("created_by"),
            "created_at": deleted_smart_link.get("created_at"),
            "updated_by": deleted_smart_link.get("updated_by"),
            "updated_at": deleted_smart_link.get("updated_at"),
            "_deleted": True,
        }

        return json.dumps(output_embed_block)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "remove_embed_block",
                "description": (
                    "Permanently deletes an embed block"
                    "This operation cannot be undone."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "embed_block_id": {
                            "type": "string",
                            "description": (
                                "The ID of the embed block to permanently delete (required)."
                            ),
                        },
                    },
                    "required": ["embed_block_id"],
                },
            },
        }

