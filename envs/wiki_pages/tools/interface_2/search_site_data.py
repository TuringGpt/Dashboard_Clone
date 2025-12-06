import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class SearchSiteData(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        site_id: Optional[str] = None,
        site_url: Optional[str] = None,
        site_name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> str:
        """
        Retrieve site details from the Confluence database.
        """
        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data format"})

        spaces = data.get("spaces", {})
        results = []

        for sid, space_data in spaces.items():
            match = True

            if site_id and sid != site_id:
                match = False
            if site_url and space_data.get("space_key") != site_url:
                match = False
            if site_name and space_data.get("name") != site_name:
                match = False
            if description and space_data.get("description") != description:
                match = False
            if status and space_data.get("status") != status:
                match = False
            if created_by and space_data.get("created_by") != created_by:
                match = False
            if created_at and space_data.get("created_at") != created_at:
                match = False
            if updated_at and space_data.get("updated_at") != updated_at:
                match = False

            if match:
                results.append(
                    {
                        "site_id": sid,
                        "site_url": space_data.get("space_key"),
                        "site_name": space_data.get("name"),
                        "description": space_data.get("description"),
                        "type": space_data.get("type"),
                        "status": space_data.get("status"),
                        "created_by": space_data.get("created_by"),
                        "created_at": space_data.get("created_at"),
                        "updated_at": space_data.get("updated_at"),
                    }
                )

        return json.dumps({"success": True, "count": len(results), "sites": results})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "search_site_data",
                "description": "Retrieve site details. Filters by site_id,\
                    site_url, site_name, description, status ('current', 'archived'),\
                    created_by, created_at, or updated_at. Date format: YYYY-MM-DDTHH:MM:SS.\
                    Returns site information including site_id, site_url, site_name,\
                    description, type, status, created_by, created_at, and updated_at.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "site_id": {
                            "type": "string",
                            "description": "Unique site identifier",
                        },
                        "site_url": {"type": "string", "description": "Site URL key"},
                        "site_name": {
                            "type": "string",
                            "description": "Site display name",
                        },
                        "description": {
                            "type": "string",
                            "description": "Site description",
                        },
                        "status": {
                            "type": "string",
                            "description": "Site status: 'current', 'archived'",
                            "enum": ["current", "archived"],
                        },
                        "created_by": {
                            "type": "string",
                            "description": "User ID who created the site",
                        },
                        "created_at": {
                            "type": "string",
                            "description": "Site creation timestamp (YYYY-MM-DDTHH:MM:SS)",
                        },
                        "updated_at": {
                            "type": "string",
                            "description": "Site last update timestamp (YYYY-MM-DDTHH:MM:SS)",
                        },
                    },
                    "required": [],
                },
            },
        }
