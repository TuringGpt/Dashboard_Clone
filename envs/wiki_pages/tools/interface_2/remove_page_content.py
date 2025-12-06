import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class RemovePageContent(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        page_id: str,
    ) -> str:
        """
        Remove a page from the system.
        """
        if not isinstance(data, dict):
            return json.dumps({
                "success": False,
                "error": "Invalid data format"
            })
        
        pages = data.get("pages", {})
        
        if page_id not in pages:
            return json.dumps({
                "success": False,
                "error": f"Page with ID {page_id} not found"
            })
        
        deleted_page = pages.pop(page_id)
        deleted_page.pop("parent_page_id", None)
        deleted_page["site_id"] = deleted_page.pop("space_id", None)
        
        return json.dumps({
            "success": True,
            "message": f"Page {page_id} removed successfully",
            "deleted_page": deleted_page
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "remove_page_content",
                "description": "Remove an existing page from the system. Deletes the page record.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page to remove"
                        }
                    },
                    "required": ["page_id"]
                }
            }
        }