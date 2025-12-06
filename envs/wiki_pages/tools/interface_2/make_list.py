import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class MakeList(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        title: str,
        site_id: str,
        created_by: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new list.
        
        Args:
            data: Environment data
            title: Title of the list (required)
            site_id: Site ID where list is hosted (required)
            created_by: User ID who created the list (required)
            schema: List of field definitions for the list (optional)
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
        if not title or not site_id or not created_by:
            return json.dumps({
                "error": "title, site_id, and created_by are required parameters"
            })
        
        # Get tables
        databases = data.get("databases", {})
        users = data.get("users", {})
        spaces = data.get("spaces", {})
        
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
        
        # Validate site_id (space) exists
        if site_id not in spaces:
            return json.dumps({
                "error": f"Site with ID {site_id} not found"
            })
        
        host_page_id = schema.get("host_page_id") if schema else None
        description = schema.get("description") if schema else None
        
        # Generate new database ID
        database_id = generate_id(databases)
        
        # Create database record
        database = {
            "database_id": database_id,
            "title": title,
            "host_space_id": site_id,
            "host_page_id": host_page_id,
            "description": description,
            "status": "current",
            "created_by": created_by,
            "created_at": "2025-12-02T12:00:00",
            "updated_by": created_by,
            "updated_at": "2025-12-02T12:00:00"
        }
        
        # Add to data
        databases[database_id] = database
        
        return json.dumps({
            "list_id": database_id,
            "title": title,
            "host_site_id": site_id,
            # "host_page_id": host_page_id, NO NEED FOR PAGE ID AS THE CONTAINER FOR LIST IS site(space)
            "description": description,
            "status": "current",
            "created_by": created_by,
            "created_at": "2025-12-02T12:00:00",
            "updated_by": created_by,
            "updated_at": "2025-12-02T12:00:00"
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "make_list",
                "description": "Create a new list. Requires title, site_id (space ID), and created_by. Optional schema field for defining list structure.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the list"
                        },
                        "site_id": {
                            "type": "string",
                            "description": "Site ID where list is hosted"
                        },
                        "created_by": {
                            "type": "string",
                            "description": "User ID who created the list"
                        },
                        "schema": {
                            "type": "array",
                            "description": "Dictionary of field definitions for the list",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "host_page_id": {
                                        "type": "string",
                                        "description": "Page ID where list is hosted"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Description of the list"
                                    }
                                }
                            }
                        }
                    },
                    "required": ["title", "site_id", "created_by"]
                }
            }
        }
