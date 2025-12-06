import json
from typing import Any, Dict, List
from tau_bench.envs.tool import Tool

class ReviseQuickLinks(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        page_id: str,
        quick_links_id: str,
        updated_by: str,
        links: List[Dict[str, Any]]
    ) -> str:
        """
        Update existing quick links (smart links).
        
        Args:
            data: Environment data
            page_id: Page ID where quick links exist (required)
            quick_links_id: ID of the quick links component to update (required)
            updated_by: User ID who is updating the links (required)
            links: New list of link objects with title, url, target_id, target_type (required)
        """
        # Validate required fields
        if not page_id or not quick_links_id or not updated_by or not links:
            return json.dumps({
                "error": "page_id, quick_links_id, updated_by, and links are required parameters"
            })
        
        # Validate links is a list
        if not isinstance(links, list):
            return json.dumps({
                "error": "links must be a list of link objects"
            })
        
        # Validate each link has required fields
        for i, link in enumerate(links):
            if not isinstance(link, dict):
                return json.dumps({
                    "error": f"Link at index {i} must be a dictionary"
                })
            
            required_fields = ["title", "url", "target_id", "target_type"]
            missing_fields = [field for field in required_fields if field not in link]
            if missing_fields:
                return json.dumps({
                    "error": f"Link at index {i} missing required fields: {', '.join(missing_fields)}"
                })
            
            # Validate target_type
            if link["target_type"] not in ["page", "database", "whiteboard", "external"]:
                return json.dumps({
                    "error": f"Link at index {i} has invalid target_type. Must be: 'page', 'database', 'whiteboard', 'external'"
                })
        
        # Get tables
        smart_links = data.get("smart_links", {})
        users = data.get("users", {})
        pages = data.get("pages", {})
        
        # Validate updated_by user exists
        if updated_by not in users:
            return json.dumps({
                "error": f"User with ID {updated_by} not found"
            })
        
        # Validate page exists
        if page_id not in pages:
            return json.dumps({
                "error": f"Page with ID {page_id} not found"
            })
        
        # Find and delete existing smart links for this quick_links_id
        # Note: In a real system, quick_links_id would be a component ID
        # For this implementation, we'll assume it's used to group related smart links
        existing_links = []
        links_to_delete = []
        
        for link_id, smart_link in smart_links.items():
            if smart_link.get("host_page_id") == page_id:
                # In a real system, we'd check a component_id field
                # For now, we'll update all smart links on the page
                existing_links.append(smart_link)
                links_to_delete.append(link_id)
        
        # Delete existing links
        for link_id in links_to_delete:
            del smart_links[link_id]
        
        # Create new smart links
        created_links = []
        
        for link in links:
            # Generate new ID
            new_id = str(max([int(k) for k in smart_links.keys()] + [0]) + 1)
            
            smart_link = {
                "smart_link_id": new_id,
                "title": link["title"],
                "url": link["url"],
                "target_id": link["target_id"],
                "target_type": link["target_type"],
                "host_page_id": page_id,
                "created_by": updated_by,  # Use updated_by as creator for new links
                "created_at": "2025-10-01T00:00:00",
                "updated_by": updated_by,
                "updated_at": "2025-10-01T00:00:00"
            }
            
            # Add to data
            smart_links[new_id] = smart_link
            created_links.append(smart_link)
        
        return json.dumps({
            "page_id": page_id,
            "quick_links_id": quick_links_id,
            "updated_by": updated_by,
            "old_links": existing_links,
            "new_links": created_links,
            "count": len(created_links)
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "revise_quick_links",
                "description": "Update existing quick links (smart links). Requires page_id, quick_links_id, updated_by, and links array. Each link must have title, url, target_id, and target_type. Target_type values: 'page', 'database', 'whiteboard', 'external'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "Page ID where quick links exist"
                        },
                        "quick_links_id": {
                            "type": "string",
                            "description": "ID of the quick links component to update"
                        },
                        "updated_by": {
                            "type": "string",
                            "description": "User ID who is updating the links"
                        },
                        "links": {
                            "type": "array",
                            "description": "New list of link objects with title, url, target_id, target_type",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "target_id": {"type": "string"},
                                    "target_type": {"type": "string", "enum": ["page", "database", "whiteboard", "external"]}
                                },
                                "required": ["title", "url", "target_id", "target_type"]
                            }
                        }
                    },
                    "required": ["page_id", "quick_links_id", "updated_by", "links"]
                }
            }
        }
