import json
from typing import Any, Dict, List
from tau_bench.envs.tool import Tool

class GenerateQuickLinks(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        page_id: str,
        created_by: str,
        links: List[Dict[str, Any]]
    ) -> str:
        """
        Create quick links on a page.
        
        Args:
            data: Environment data
            page_id: Page ID where quick links will be created (required)
            created_by: User ID who created the links (required)
            links: List of link objects with title, url, target_id, target_type (required)
        """
        def generate_id(table: Dict[str, Any]) -> str:
            """Generate a new unique ID for a record."""
            if not table:
                return "1"
            try:
                return str(max(int(k) for k in table.keys()) + 1)
            except ValueError:
                return "1"
        
        # Validate required fields
        if not page_id or not created_by or not links:
            return json.dumps({
                "error": "page_id, created_by, and links are required parameters"
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
            if link["target_type"] not in ["page", "database", "whiteboard", "external", "attachment"]:
                return json.dumps({
                    "error": f"Link at index {i} has invalid target_type. Must be: 'page', 'database', 'whiteboard', 'external', 'attachment'"
                })
        
        # Get tables
        smart_links = data.get("smart_links", {})
        users = data.get("users", {})
        pages = data.get("pages", {})
        
        # Validate created_by user exists
        if created_by not in users:
            return json.dumps({
                "error": f"User with ID {created_by} not found"
            })
        
        user = users.get(created_by, {})
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID {created_by} is not active"
            })
        
        # Validate page exists
        if page_id not in pages:
            return json.dumps({
                "error": f"Page with ID {page_id} not found"
            })
        
        created_links = []
        
        timestamp = "2025-12-02T12:00:00"

        # Create each smart link
        for link in links:
            smart_link_id = generate_id(smart_links)
            
            smart_link = {
                "smart_link_id": smart_link_id,
                "title": link["title"],
                "url": link["url"],
                "target_id": link["target_id"],
                "target_type": link["target_type"],
                "host_page_id": page_id,
                "created_by": created_by,
                "created_at": timestamp,
                "updated_by": created_by,
                "updated_at": timestamp
            }
            
            # Add to data
            smart_links[smart_link_id] = smart_link
            created_links.append(smart_link)
        
        return json.dumps({
            "page_id": page_id,
            "created_by": created_by,
            "links": [
                {
                    "quick_link_id": link["smart_link_id"],
                    "title": link["title"],
                    "url": link["url"],
                    "target_id": link["target_id"],
                    "target_type": link["target_type"],
                    "host_page_id": link["host_page_id"],
                    "created_by": link["created_by"],
                    "created_at": link["created_at"],
                    "updated_by": link["updated_by"],
                    "updated_at": link["updated_at"]
                }
                for link in created_links
            ],
            "count": len(created_links)
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "generate_quick_links",
                "description": "Create quick links on a page. Requires page_id, created_by, and links array. Each link must have title, url, target_id, and target_type. Target_type values: 'page', 'database', 'whiteboard', 'external', 'attachment'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "Page ID where quick links will be created"
                        },
                        "created_by": {
                            "type": "string",
                            "description": "User ID who created the links"
                        },
                        "links": {
                            "type": "array",
                            "description": "List of link objects with title, url, target_id, target_type",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "target_id": {"type": "string"},
                                    "target_type": {"type": "string", "enum": ["page", "database", "whiteboard", "external", "attachment"]}
                                },
                                "required": ["title", "url", "target_id", "target_type"]
                            }
                        }
                    },
                    "required": ["page_id", "created_by", "links"]
                }
            }
        }
