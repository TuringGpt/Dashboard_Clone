import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class ModifyPageContent(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        page_id: str,
        updated_by: str,
        title: Optional[str] = None,
        site_id: Optional[str] = None,
        body_storage: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Update an existing page.
        """
        if not isinstance(data, dict):
            return json.dumps({
                "success": False,
                "error": "Invalid data format"
            })
        
        pages = data.get("pages", {})
        spaces = data.get("spaces", {})
        users = data.get("users", {})
        
        if page_id not in pages:
            return json.dumps({
                "success": False,
                "error": f"Page with ID {page_id} not found"
            })
        
        if updated_by not in users:
            return json.dumps({
                "success": False,
                "error": f"User with ID {updated_by} not found"
            })
        
        user_info = users[updated_by]
        if user_info.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID {updated_by} is not active"
            })
        
        if site_id and site_id not in spaces:
            return json.dumps({
                "success": False,
                "error": f"Site with ID {site_id} not found"
            })
        
        VALID_STATUS = {"current", "draft", "locked", "archived", "deleted"}
        if status is not None and status not in VALID_STATUS:
            return json.dumps({
                "success": False,
                "error": f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUS)}"
            })
        
        page = pages[page_id]
        timestamp = "2025-12-02T12:00:00"
        
        if title:
            page["title"] = title
        if site_id:
            page["space_id"] = site_id
        if body_storage is not None:
            page["body_storage"] = body_storage
        if status:
            page["status"] = status
        
        page["updated_by"] = updated_by
        page["updated_at"] = timestamp

        response = page.copy()
        response["site_id"] = response.pop("space_id", None)
        
        return json.dumps(response)
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "modify_page_content",
                "description": "Update an existing page. Requires page_id and updated_by. Optional fields include title, site_id, body_storage, and status.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "Page ID to update"
                        },
                        "updated_by": {
                            "type": "string",
                            "description": "User ID of the person updating the page"
                        },
                        "title": {
                            "type": "string",
                            "description": "Update page title"
                        },
                        "site_id": {
                            "type": "string",
                            "description": "Update site ID for the page"
                        },
                        "body_storage": {
                            "type": "string",
                            "description": "Update page content in storage format"
                        },
                        "status": {
                            "type": "string",
                            "description": "Update page status: 'current', 'draft', 'locked', 'archived', or 'deleted'"
                        }
                    },
                    "required": ["page_id", "updated_by"]
                }
            }
        }
