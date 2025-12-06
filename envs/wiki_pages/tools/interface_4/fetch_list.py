import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class FetchList(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        list_id: Optional[str] = None,
        host_doc_id: Optional[str] = None,
        title: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> str:
        """
        Obtain list(s) based on filter criteria (ClickUp logic).
        """
        databases = data.get("databases", {})
        results = []
        
        for db_id, db in databases.items():
            match = True
            
            if list_id and db_id != list_id:
                match = False
            if host_doc_id and db.get("host_page_id") != host_doc_id:
                match = False
            if title and db.get("title") != title:
                match = False
            if status and db.get("status") != status:
                match = False
            if created_by and db.get("created_by") != created_by:
                match = False
            
            if match:
                # Map database fields to interface fields
                list_obj = {
                    "list_id": db.get("database_id"),
                    "title": db.get("title"),
                    "host_space_id": db.get("host_space_id"),
                    "host_doc_id": db.get("host_page_id"),
                    "description": db.get("description"),
                    "status": db.get("status"),
                    "created_by": db.get("created_by"),
                    "created_at": db.get("created_at"),
                    "updated_by": db.get("updated_by"),
                    "updated_at": db.get("updated_at")
                }
                results.append(list_obj)
        
        return json.dumps({
            "success": True,
            "count": len(results),
            "lists": results
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "fetch_list", 
                "description": "Retrieve lists based on filter criteria such as list_id, host_doc_id, title, or status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "list_id": {
                            "type": "string",
                            "description": "Filter by list ID (optional)"
                        },
                        "host_doc_id": {
                            "type": "string",
                            "description": "Filter by host doc ID (optional)"
                        },
                        "title": {
                            "type": "string",
                            "description": "Filter by title (optional)"
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status: current, archived, deleted (optional)"
                        },
                        "created_by": {
                            "type": "string",
                            "description": "Filter by creator user ID (optional)"
                        }
                    },
                    "required": []
                }
            }
        }

