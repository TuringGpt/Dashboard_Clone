import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class GetUserPermissions(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        filter: Dict[str, Any]
    ) -> str:
        """
        Locate user permissions with cascading support.
        For Documents, includes both direct permissions and inherited permissions 
        from parent Documents and containing spaces.
        """
        email = filter.get("email")
        doc_id = filter.get("doc_id")
        space_id = filter.get("space_id")
        
        # Validate required field
        if not email:
            return json.dumps({
                "success": False,
                "error": "email is required in filter",
                "count": 0,
                "permissions": []
            })
        
        # Find user_id from email
        user_id = None
        users_table = data.get("users", {})
        for uid, user in users_table.items():
            if user.get("email") == email:
                user_id = uid
                break
        
        if not user_id:
            return json.dumps({
                "success": False,
                "error": f"User with email '{email}' not found",
                "count": 0,
                "permissions": []
            })
        
        # Validate referenced entities exist
        pages = data.get("pages", {})
        spaces = data.get("spaces", {})
        
        if doc_id and doc_id not in pages:
            return json.dumps({
                "success": False,
                "error": f"doc_id '{doc_id}' does not reference a valid Doc",
                "count": 0,
                "permissions": []
            })
        
        if space_id and space_id not in spaces:
            return json.dumps({
                "success": False,
                "error": f"space_id '{space_id}' does not reference a valid space",
                "count": 0,
                "permissions": []
            })
        
        permissions_table = data.get("permissions", {})
        matching_permissions = []
        
        # Case 1: Only email provided - return ALL permissions for this user
        if not doc_id and not space_id:
            for perm in permissions_table.values():
                if perm.get("user_id") == user_id:
                    matching_permissions.append(perm)
        
        # Case 2: Email + space_id - return only direct space permissions
        elif space_id and not doc_id:
            for perm in permissions_table.values():
                if (perm.get("user_id") == user_id and 
                    perm.get("content_type") == "space" and 
                    perm.get("content_id") == space_id):
                    matching_permissions.append(perm)
        
        # Case 3: Email + doc_id - return direct + inherited permissions
        elif doc_id:
            # Direct permissions on the page
            for perm in permissions_table.values():
                if (perm.get("user_id") == user_id and 
                    perm.get("content_type") == "page" and 
                    perm.get("content_id") == doc_id):
                    matching_permissions.append(perm)
            
            # Cascade: traverse up the page hierarchy to find inherited permissions
            def get_ancestors(page_id: str) -> list:
                """Returns list of ancestor IDs: [(type, id), ...]"""
                ancestors = []
                current_page_id = page_id
                visited = set()
                
                while current_page_id and current_page_id not in visited:
                    visited.add(current_page_id)
                    page_data = pages.get(current_page_id)
                    
                    if not page_data:
                        break
                    
                    parent_page_id = page_data.get("parent_page_id")
                    
                    if parent_page_id:
                        ancestors.append(("page", str(parent_page_id)))
                        current_page_id = str(parent_page_id)
                    else:
                        # No parent page, so add the space and stop
                        page_space_id = page_data.get("space_id")
                        if page_space_id:
                            ancestors.append(("space", str(page_space_id)))
                        break
                
                return ancestors
            
            # Get all ancestors
            ancestors = get_ancestors(doc_id)
            
            # Check permissions for each ancestor in order
            for content_type, content_id in ancestors:
                inherited_perms = [
                    perm
                    for perm in permissions_table.values()
                    if str(perm.get("user_id")) == user_id
                    and str(perm.get("content_type")) == content_type
                    and str(perm.get("content_id")) == content_id
                ]
                matching_permissions.extend(inherited_perms)
        
        # Map database fields to interface fields for all permissions
        response_permissions = []
        for perm in matching_permissions:
            response_perm = {
                "permission_id": perm.get("permission_id"),
                "user_id": perm.get("user_id"),
                "operation": perm.get("operation"),
                "granted_by": perm.get("granted_by"),
                "granted_at": perm.get("granted_at")
            }
            # Map content_id and content_type based on type
            if perm.get("content_type") == "page":
                response_perm["doc_id"] = perm.get("content_id")
                response_perm["content_type"] = "doc"
            elif perm.get("content_type") == "space":
                response_perm["space_id"] = perm.get("content_id")
                response_perm["content_type"] = "space"
            else:
                # Keep original if unknown type
                response_perm["content_id"] = perm.get("content_id")
                response_perm["content_type"] = perm.get("content_type")
            
            response_permissions.append(response_perm)
        
        return json.dumps({
            "success": True, 
            "count": len(response_permissions), 
            "permissions": response_permissions
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_user_permissions",
                "description": "Get user permissions for docs and spaces. Filter by email (required), and optionally by doc_id (includes inherited permissions) or space_id (direct permissions only).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "object",
                            "properties": {
                                "email": {
                                    "type": "string", 
                                    "description": "Email address of the user (required)"
                                },
                                "doc_id": {
                                    "type": "string", 
                                    "description": "ID of the document (optional). When provided, includes inherited permissions from parent Document and space."
                                },
                                "space_id": {
                                    "type": "string", 
                                    "description": "ID of the space (optional). When provided, only returns direct space permissions."
                                }
                            },
                            "required": ["email"]
                        }
                    },
                    "required": ["filter"]
                }
            }
        }