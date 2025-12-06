import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class CreateDoc(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        fields: Dict[str, Any]
    ) -> str:
        """
        Construct a new doc in the specified space (ClickUp logic).
        Wraps arguments in a 'fields' dictionary as per documentation.
        """
        # Unwrap fields
        space_id = fields.get("space_id")
        title = fields.get("title")
        body_storage = fields.get("body_storage")
        status = fields.get("status")
        created_by = fields.get("created_by")

        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)
        
        timestamp = "2025-12-02T12:00:00"
        pages = data.get("pages", {})
        spaces = data.get("spaces", {})
        users = data.get("users", {})
        
        # Validate required parameters
        if not all([space_id, title, created_by]):
            return json.dumps({
                "success": False,
                "error": "Missing required fields in 'fields' dict: space_id, title, and created_by are required"
            })
        
        # Validate space exists
        if space_id not in spaces:
            return json.dumps({
                "success": False,
                "error": f"Space with ID '{space_id}' not found"
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
        
        # Validate status if provided
        valid_statuses = ["current", "draft", "locked", "archived", "deleted"]
        if status and status not in valid_statuses:
            return json.dumps({
                "success": False,
                "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            })
        
        # Generate new page ID
        new_page_id = generate_id(pages)
        
        # Create new page (doc)
        new_page = {
            "page_id": new_page_id,
            "title": title,
            "space_id": space_id,
            "parent_page_id": None,
            "body_storage": body_storage,
            "status": status if status else "current",
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp
        }
        
        pages[new_page_id] = new_page
        
        return json.dumps(new_page)
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_doc", 
                "description": "Construct a new doc in a specified space. Requires a 'fields' object containing space_id, title, and created_by.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "properties": {
                                "space_id": {
                                    "type": "string",
                                    "description": "ID of the space where the doc will be created"
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Title of the doc"
                                },
                                "body_storage": {
                                    "type": "string",
                                    "description": "Content of the doc in storage format (optional)"
                                },
                                "status": {
                                    "type": "string",
                                    "description": "Status of the doc: current, draft, locked, archived, deleted (optional, defaults to current)",
                                    "enum": ["current", "draft", "locked", "archived", "deleted"]
                                },
                                "created_by": {
                                    "type": "string",
                                    "description": "User ID of the doc creator"
                                }
                            },
                            "required": ["space_id", "title", "created_by"]
                        }
                    },
                    "required": ["fields"]
                }
            }
        }
