import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class UpdateLinksField(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        fields: Dict[str, Any]
    ) -> str:
        """
        Replace an embedded link on a doc (ClickUp logic).
        Wraps arguments in a 'fields' dictionary as per documentation.
        """
        # Unwrap fields
        embed_link_id = fields.get("embed_link_id")
        url = fields.get("url")
        title = fields.get("title")
        updated_by = fields.get("updated_by")
        
        timestamp = "2025-12-02T12:00:00"
        smart_links = data.get("smart_links", {})
        users = data.get("users", {})
        
        # Validate required parameters
        if not embed_link_id or not updated_by:
            return json.dumps({
                "success": False,
                "error": "Missing required fields in 'fields' dict: embed_link_id and updated_by are required"
            })
        
        # Validate embed link exists
        if embed_link_id not in smart_links:
            return json.dumps({
                "success": False,
                "error": f"Embedded link with ID '{embed_link_id}' not found"
            })
        
        # Validate user exists
        if updated_by not in users:
            return json.dumps({
                "success": False,
                "error": f"User with ID '{updated_by}' not found"
            })
        
        user = users[updated_by]
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID '{updated_by}' is not active"
            })
        
        # Update the embedded link
        link = smart_links[embed_link_id]
        
        if url is not None:
            link["url"] = url
        if title is not None:
            link["title"] = title
        
        link["updated_by"] = updated_by
        link["updated_at"] = timestamp
        
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
            "embed_link_id": link.get("smart_link_id"),
            "title": link.get("title"),
            "url": link.get("url"),
            "target_id": link.get("target_id"),
            "target_type": map_target_type(link.get("target_type")),
            "host_doc_id": link.get("host_page_id"),
            "created_by": link.get("created_by"),
            "created_at": link.get("created_at"),
            "updated_by": link.get("updated_by"),
            "updated_at": link.get("updated_at")
        }
        
        return json.dumps({
            "success": True,
            "embed_link": response_link
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "update_links_field", 
                "description": "Update an existing embedded link's URL or title on a doc. Requires a 'fields' object containing embed_link_id and updated_by",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "properties": {
                                "embed_link_id": {
                                    "type": "string",
                                    "description": "ID of the embedded link to update"
                                },
                                "url": {
                                    "type": "string",
                                    "description": "New URL for the embedded link (optional)"
                                },
                                "title": {
                                    "type": "string",
                                    "description": "New title for the embedded link (optional)"
                                },
                                "updated_by": {
                                    "type": "string",
                                    "description": "User ID of the person updating the link"
                                }
                            },
                            "required": ["embed_link_id", "updated_by"]
                        }
                    },
                    "required": ["fields"]
                }
            }
        }

