import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class FetchEffectivePermissions(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        user_id: str,
        page_id: Optional[str] = None,
        site_id: Optional[str] = None,
    ) -> str:
        """
        Fetch effective permissions for a user on a specific page or site.
        """
        if not isinstance(data, dict):
            return json.dumps({
                "success": False,
                "error": "Invalid data format"
            })
        
        users = data.get("users", {})
        pages = data.get("pages", {})
        permissions = data.get("permissions", {})
        
        if user_id not in users:
            return json.dumps({
                "success": False,
                "error": f"User with ID {user_id} not found"
            })
        
        user = users.get(user_id, {})
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID {user_id} is not active"
            })
        
        if not page_id and not site_id:
            return json.dumps({
                "success": True,
                "user_id": user_id,
                "page_id": None,
                "site_id": None,
                "content_id": None,
                "content_type": None,
                "count": 0,
                "permissions": []
            })

        if page_id and site_id:
            if page_id not in pages:
                return json.dumps({
                    "success": False,
                    "error": f"Page with ID {page_id} not found"
                })
            page_space = pages[page_id].get("space_id")
            if page_space != site_id:
                return json.dumps({
                    "success": False,
                    "error": "Provided page_id does not belong to the provided site_id"
                })

        # Determine content target
        if page_id:
            content_id = page_id
            content_type = "page"
        else:
            content_id = site_id
            content_type = "site"   # FIX: return 'site' instead of 'space'

        # Collect permissions
        user_permissions = []
        for perm_id, perm_data in permissions.items():
            # Internal DB still stores content_type=space, but input returns site
            internal_content_type = perm_data.get("content_type")
            matches_type = (
                (content_type == "page" and internal_content_type == "page") or
                (content_type == "site" and internal_content_type == "space")
            )

            if (
                matches_type and
                perm_data.get("content_id") == content_id and
                perm_data.get("user_id") == user_id
            ):
                user_permissions.append({**perm_data, "permission_id": perm_id})
        
        return json.dumps({
            "success": True,
            "user_id": user_id,
            "page_id": page_id,
            "site_id": site_id,
            "content_id": content_id,
            "content_type": content_type,
            "count": len(user_permissions),
            "permissions": user_permissions
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "fetch_effective_permissions",
                "description": "Fetch effective permissions for a user on a specific page or site. Returns all permissions granted to the user for the specified content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID to check permissions for"
                        },
                        "page_id": {
                            "type": "string",
                            "description": "Page ID to check permissions on (mutually exclusive with site_id)"
                        },
                        "site_id": {
                            "type": "string",
                            "description": "Site ID to check permissions on (mutually exclusive with page_id)"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        }
