import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class UpdateDoc(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        doc_id: str,
        updated_by: str,
        title: Optional[str] = None,
        space_id: Optional[str] = None,
        body_storage: Optional[str] = None,
        status: Optional[str] = None
    ) -> str:
        """
        Adjust an existing doc (ClickUp logic).
        """
        timestamp = "2025-12-02T12:00:00"
        pages = data.get("pages", {})
        users = data.get("users", {})
        spaces = data.get("spaces", {})
        
        # Validate required parameters
        if not doc_id or not updated_by:
            return json.dumps({
                "success": False,
                "error": "Missing required parameters: doc_id and updated_by are required"
            })
        
        # Validate doc exists
        if doc_id not in pages:
            return json.dumps({
                "success": False,
                "error": f"Doc with ID '{doc_id}' not found"
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
        
        # Validate space if provided
        if space_id is not None and space_id not in spaces:
            return json.dumps({
                "success": False,
                "error": f"Space with ID '{space_id}' not found"
            })
        
        # Validate status if provided
        valid_statuses = ["current", "draft", "locked", "archived", "deleted"]
        if status and status not in valid_statuses:
            return json.dumps({
                "success": False,
                "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            })
        
        # Update the doc
        doc = pages[doc_id]
        
        if title is not None:
            doc["title"] = title
        if space_id is not None:
            doc["space_id"] = space_id
        if body_storage is not None:
            doc["body_storage"] = body_storage
        if status is not None:
            doc["status"] = status
        
        doc["updated_by"] = updated_by
        doc["updated_at"] = timestamp
        
        # Map database fields to interface fields
        response_doc = {
            "doc_id": doc.get("page_id"),
            "title": doc.get("title"),
            "space_id": doc.get("space_id"),
            "parent_doc_id": doc.get("parent_page_id"),
            "body_storage": doc.get("body_storage"),
            "status": doc.get("status"),
            "created_by": doc.get("created_by"),
            "created_at": doc.get("created_at"),
            "updated_by": doc.get("updated_by"),
            "updated_at": doc.get("updated_at")
        }
        
        return json.dumps({
            "success": True,
            "doc": response_doc
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "update_doc", 
                "description": "Update an existing doc's properties such as title, space, content, or status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "ID of the doc to adjust"
                        },
                        "updated_by": {
                            "type": "string",
                            "description": "User ID of the person updating the doc"
                        },
                        "title": {
                            "type": "string",
                            "description": "New title for the doc (optional)"
                        },
                        "space_id": {
                            "type": "string",
                            "description": "New space ID for the doc (optional)"
                        },
                        "body_storage": {
                            "type": "string",
                            "description": "New content for the doc in storage format (optional)"
                        },
                        "status": {
                            "type": "string",
                            "description": "New status: current, draft, locked, archived, deleted (optional)",
                            "enum": ["current", "draft", "locked", "archived", "deleted"]
                        }
                    },
                    "required": ["doc_id", "updated_by"]
                }
            }
        }

