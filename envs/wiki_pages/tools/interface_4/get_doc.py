import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class GetDoc(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        doc_id: Optional[str] = None,
        space_id: Optional[str] = None,
        title: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> str:
        """
        Get doc(s) based on filter criteria.
        """
        pages = data.get("pages", {})
        spaces = data.get("spaces", {})
        users = data.get("users", {})
        page_labels = data.get("page_labels", {})
        smart_links = data.get("smart_links", {})
        results = []
        
        # Validate space_id if provided
        if space_id and space_id not in spaces:
            return json.dumps({
                "success": False,
                "error": f"space_id '{space_id}' does not reference a valid space",
                "count": 0,
                "docs": []
            })
        
        # Validate created_by if provided
        if created_by and created_by not in users:
            return json.dumps({
                "success": False,
                "error": f"created_by '{created_by}' does not reference a valid user",
                "count": 0,
                "docs": []
            })
        
        # Validate updated_by if provided
        if updated_by and updated_by not in users:
            return json.dumps({
                "success": False,
                "error": f"updated_by '{updated_by}' does not reference a valid user",
                "count": 0,
                "docs": []
            })
        
        # Build indexes for labels and smart_links by page_id for O(1) lookup
        labels_by_page = {}
        for label_id, label in page_labels.items():
            page_id = label.get("page_id")
            if page_id not in labels_by_page:
                labels_by_page[page_id] = []
            labels_by_page[page_id].append(label)
        
        links_by_page = {}
        for link_id, link in smart_links.items():
            page_id = link.get("host_page_id")
            if page_id not in links_by_page:
                links_by_page[page_id] = []
            links_by_page[page_id].append(link)
        
        for page_id, page in pages.items():
            match = True
            
            if doc_id and page_id != doc_id:
                match = False
            if space_id and page.get("space_id") != space_id:
                match = False
            if title and page.get("title") != title:
                match = False
            if status and page.get("status") != status:
                match = False
            if created_by and page.get("created_by") != created_by:
                match = False
            if updated_by and page.get("updated_by") != updated_by:
                match = False
            
            if match:
                # Create a copy of the page to avoid modifying the original
                page_with_relations = page.copy()
                
                # Add labels and smart_links using the pre-built indexes
                page_with_relations["labels"] = labels_by_page.get(page_id, [])
                page_with_relations["smart_links"] = links_by_page.get(page_id, [])
                
                results.append(page_with_relations)
        
        return json.dumps({
            "success": True,
            "count": len(results),
            "docs": results
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_doc", 
                "description": "Get doc(s) based on filter criteria. Returns all docs that match the specified filters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "Filter by doc ID (optional)"
                        },
                        "space_id": {
                            "type": "string",
                            "description": "Filter by space ID (optional)"
                        },
                        "title": {
                            "type": "string",
                            "description": "Filter by title (optional)"
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status: current, draft, locked, archived, deleted (optional)"
                        },
                        "created_by": {
                            "type": "string",
                            "description": "Filter by creator user ID (optional)"
                        },
                        "updated_by": {
                            "type": "string",
                            "description": "Filter by updater user ID (optional)"
                        }
                    },
                    "required": []
                }
            }
        }