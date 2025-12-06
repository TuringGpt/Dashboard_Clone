import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class DiscoverPage(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        page_id: Optional[str] = None,
        title: Optional[str] = None,
        site_id: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_by: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> str:
        """
        Get pages with detailed filtering options.
        """
        if not isinstance(data, dict):
            return json.dumps({
                "success": False,
                "error": "Invalid data format for pages"
            })
        
        pages = data.get("pages", {})
        results = []
        
        for pid, page_data in pages.items():
            if page_id and pid != page_id:
                continue
            if title and page_data.get("title") != title:
                continue
            if site_id and page_data.get("space_id") != site_id:
                continue
            if status and page_data.get("status") != status:
                continue
            if created_by and page_data.get("created_by") != created_by:
                continue
            if created_at and page_data.get("created_at") != created_at:
                continue
            if updated_by and page_data.get("updated_by") != updated_by:
                continue
            if updated_at and page_data.get("updated_at") != updated_at:
                continue
            
            # results.append({**page_data, "page_id": pid})
            result_entry = {
                **page_data,
                "page_id": pid,
                "site_id": page_data.get("space_id")
            }
            result_entry.pop("space_id", None)  # remove raw db field
            
            results.append(result_entry)
        
        return json.dumps({
            "success": True,
            "count": len(results),
            "results": results
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "discover_page",
                "description": "Retrieve page details.\
                    Filters by page_id, title, site_id,\
                    parent_page_id, status ('current', 'draft', 'locked', 'archived', 'deleted'),\
                    created_by, created_at, updated_by, or updated_at.\
                    Date format: YYYY-MM-DDTHH:MM:SS.\
                    Returns page information including page_id, title, site_id, parent_page_id,\
                    body_storage, status, created_by, created_at, updated_by, and updated_at.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "Page ID to search for"
                        },
                        "title": {
                            "type": "string",
                            "description": "Page title to search for"
                        },
                        "site_id": {
                            "type": "string",
                            "description": "Space ID the page belongs to"
                        },
                        "status": {
                            "type": "string",
                            "description": "Page status: 'current', 'draft', 'locked', 'archived', or 'deleted'"
                        },
                        "created_by": {
                            "type": "string",
                            "description": "User ID of the page creator"
                        },
                        "created_at": {
                            "type": "string",
                            "description": "Creation timestamp in format YYYY-MM-DDTHH:MM:SS"
                        },
                        "updated_by": {
                            "type": "string",
                            "description": "User ID of the last person who updated the page"
                        },
                        "updated_at": {
                            "type": "string",
                            "description": "Last update timestamp in format YYYY-MM-DDTHH:MM:SS"
                        }
                    },
                    "required": [],
                },
            },
        }