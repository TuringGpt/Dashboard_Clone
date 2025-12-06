import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteLinksField(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        embed_link_id: str
    ) -> str:
        """
        Remove an embedded link from a doc (ClickUp logic).
        """
        smart_links = data.get("smart_links", {})
        
        # Validate required parameters
        if not embed_link_id:
            return json.dumps({
                "success": False,
                "error": "Missing required parameter: embed_link_id"
            })
        
        # Validate embed link exists
        if embed_link_id not in smart_links:
            return json.dumps({
                "success": False,
                "error": f"Embedded link with ID '{embed_link_id}' not found"
            })
        
        # Delete the embedded link
        deleted_link = smart_links.pop(embed_link_id)
        
        # Map target_type from database to interface terminology
        def map_target_type(db_type):
            mapping = {
                "page": "doc",
                "database": "list",
                "whiteboard": "whiteboard",
                "external": "external",
                "attachment": "attachment"
            }
            return mapping.get(db_type, db_type)
        
        # Map database fields to interface fields
        response_link = {
            "embed_link_id": deleted_link.get("smart_link_id"),
            "title": deleted_link.get("title"),
            "url": deleted_link.get("url"),
            "target_id": deleted_link.get("target_id"),
            "target_type": map_target_type(deleted_link.get("target_type")),
            "host_doc_id": deleted_link.get("host_page_id"),
            "created_by": deleted_link.get("created_by"),
            "created_at": deleted_link.get("created_at"),
            "updated_by": deleted_link.get("updated_by"),
            "updated_at": deleted_link.get("updated_at")
        }
        
        return json.dumps({
            "success": True,
            "message": f"Embedded link with ID '{embed_link_id}' has been removed",
            "deleted_embed_link": response_link
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_links_field", 
                "description": "Permanently delete an embedded link from a doc by embed_link_id",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "embed_link_id": {
                            "type": "string",
                            "description": "ID of the embedded link to remove"
                        }
                    },
                    "required": ["embed_link_id"]
                }
            }
        }

