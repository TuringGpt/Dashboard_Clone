import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class ModifyList(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        list_id: str,
        updated_by: str,
        title: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Adjust an existing list.
        
        Args:
            data: Environment data
            list_id: ID of the list to adjust (required)
            updated_by: User ID who is updating the list (required)
            title: New title for the list (optional)
            settings: New settings for the list (optional)
        """
        # Get tables
        databases = data.get("databases", {})
        users = data.get("users", {})
        
        # Validate required fields
        if not list_id or not updated_by:
            return json.dumps({
                "error": "list_id and updated_by are required parameters"
            })
        
        # Validate database exists
        if list_id not in databases:
            return json.dumps({
                "error": f"List with ID {list_id} not found"
            })
        
        # Validate updated_by user exists
        if updated_by not in users:
            return json.dumps({
                "error": f"User with ID {updated_by} not found"
            })
        
        # Validate user is active
        user = users.get(updated_by, {})
        if user.get("status") != "active":
            return json.dumps({
                "error": f"User with ID {updated_by} is not active"
            })
        
        # Check if at least one field to update is provided
        if title is None and settings is None:
            return json.dumps({
                "error": "At least one of title or settings must be provided for update"
            })
        
        # Get current database
        database = databases[list_id].copy()
        
        # Check if database is not deleted
        if database.get("status") == "deleted":
            return json.dumps({
                "error": f"List with ID {list_id} has been deleted"
            })
        
        # Update fields if provided
        if title is not None:
            database["title"] = title
        
        if settings is not None:
            allowed = {"description", "status"}
            clean_settings = {k: v for k, v in settings.items() if k in allowed}

            # Validate status enum
            if "status" in clean_settings:
                allowed_status = {"current", "archived", "deleted"}
                new_status = clean_settings["status"]

                if new_status not in allowed_status:
                    return json.dumps({
                        "error": f"Invalid status '{new_status}'. Allowed values: current, archived, deleted"
                    })

            for key, value in clean_settings.items():
                database[key] = value
        
        # Update metadata
        database["updated_by"] = updated_by
        database["updated_at"] = "2025-12-02T12:00:00"
        
        # Save back to data
        databases[list_id] = database

        response = {
            "list_id": list_id,
            "host_site_id": database.get("host_space_id"),
            # "host_page_id": database.get("host_page_id"), # NO NEED FOR PAGE ID AS THE CONTAINER FOR LIST IS site(space)
            "title": database.get("title"),
            "description": database.get("description"),
            "status": database.get("status"),
            "updated_by": database.get("updated_by"),
            "updated_at": database.get("updated_at")
        }
        
        return json.dumps(response)
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "modify_list",
                "description": "Adjust an existing list. Requires list_id and updated_by. At least one of title or settings must be provided for update.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "list_id": {
                            "type": "string",
                            "description": "ID of the list to adjust"
                        },
                        "updated_by": {
                            "type": "string",
                            "description": "User ID who is updating the list"
                        },
                        "title": {
                            "type": "string",
                            "description": "Update title for the list"
                        },
                        "settings": {
                            "type": "object",
                            "description": "Allowed settings fields for update: description, status"
                        }
                    },
                    "required": ["list_id", "updated_by"]
                }
            }
        }
