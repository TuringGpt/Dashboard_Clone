import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class SetLinksField(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        host_doc_id: str,
        url: str,
        title: str,
        target_type: Optional[str] = None,
        created_by: str = None
    ) -> str:
        """
        Set an embedded link on a doc (ClickUp logic).
        """
        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)
        
        timestamp = "2025-12-02T12:00:00"
        smart_links = data.get("smart_links", {})
        pages = data.get("pages", {})
        users = data.get("users", {})
        
        # Validate required parameters
        if not all([host_doc_id, url, title, created_by]):
            return json.dumps({
                "success": False,
                "error": "Missing required parameters: host_doc_id, url, title, and created_by are required"
            })
        
        # Validate doc exists
        if host_doc_id not in pages:
            return json.dumps({
                "success": False,
                "error": f"Doc with ID '{host_doc_id}' not found"
            })
        
        # Validate user exists
        if created_by not in users:
            return json.dumps({
                "success": False,
                "error": f"User with ID '{created_by}' not found"
            })
        
        user = users[created_by]
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID '{created_by}' is not active"
            })
        
        # Validate target_type if provided
        valid_target_types = ["doc", "list", "whiteboard", "external", "attachment"]
        if target_type and target_type not in valid_target_types:
            return json.dumps({
                "success": False,
                "error": f"Invalid target_type. Must be one of: {', '.join(valid_target_types)}"
            })
        
        # Map interface terminology to database terminology
        def map_to_db_target_type(interface_type):
            mapping = {
                "doc": "page",
                "list": "database",
                "whiteboard": "whiteboard",
                "external": "external",
                "attachment": "attachment"
            }
            return mapping.get(interface_type, interface_type)
        
        # Map database terminology to interface terminology
        def map_to_interface_target_type(db_type):
            mapping = {
                "page": "doc",
                "database": "list",
                "whiteboard": "whiteboard",
                "external": "external",
                "attachment": "attachment"
            }
            return mapping.get(db_type, db_type)
        
        # Generate new smart link ID
        new_link_id = generate_id(smart_links)
        
        db_target_type = map_to_db_target_type(target_type) if target_type else "external"
        
        # Create new smart link for database (using database field names)
        db_link = {
            "smart_link_id": new_link_id,
            "title": title,
            "url": url,
            "target_id": None,
            "target_type": db_target_type,
            "host_page_id": host_doc_id,
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp
        }
        
        smart_links[new_link_id] = db_link
        
        # Create response object with interface field names
        response_link = {
            "embed_link_id": new_link_id,
            "title": title,
            "url": url,
            "target_id": None,
            "target_type": target_type if target_type else "external",
            "host_doc_id": host_doc_id,
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp
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
                "name": "set_links_field", 
                "description": "Add a new embedded link to a doc with URL, title, and target type",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "host_doc_id": {
                            "type": "string",
                            "description": "ID of the doc where the link will be embedded"
                        },
                        "url": {
                            "type": "string",
                            "description": "URL of the embedded link"
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the embedded link"
                        },
                        "target_type": {
                            "type": "string",
                            "description": "Type of target: doc, list, whiteboard, external, attachment (optional, defaults to external)",
                            "enum": ["doc", "list", "whiteboard", "external", "attachment"]
                        },
                        "created_by": {
                            "type": "string",
                            "description": "User ID of the person creating the link"
                        }
                    },
                    "required": ["host_doc_id", "url", "title", "created_by"]
                }
            }
        }

