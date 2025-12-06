import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteDoc(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        doc_id: str
    ) -> str:
        """
        Destroy a doc (ClickUp logic).
        """
        pages = data.get("pages", {})
        
        # Validate required parameters
        if not doc_id:
            return json.dumps({
                "success": False,
                "error": "Missing required parameter: doc_id"
            })
        
        # Validate doc exists
        if doc_id not in pages:
            return json.dumps({
                "success": False,
                "error": f"Doc with ID '{doc_id}' not found"
            })
        
        # Delete the page
        deleted_page = pages.pop(doc_id)
        
        # Map database fields to interface fields
        response_doc = {
            "doc_id": deleted_page.get("page_id"),
            "title": deleted_page.get("title"),
            "space_id": deleted_page.get("space_id"),
            "body_storage": deleted_page.get("body_storage"),
            "status": deleted_page.get("status"),
            "created_by": deleted_page.get("created_by"),
            "created_at": deleted_page.get("created_at"),
            "updated_by": deleted_page.get("updated_by"),
            "updated_at": deleted_page.get("updated_at")
        }
        
        return json.dumps({
            "success": True,
            "message": f"Doc with ID '{doc_id}' has been destroyed",
            "deleted_doc": response_doc
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_doc", 
                "description": "Permanently delete a doc from the system by doc_id",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "ID of the doc to destroy"
                        }
                    },
                    "required": ["doc_id"]
                }
            }
        }