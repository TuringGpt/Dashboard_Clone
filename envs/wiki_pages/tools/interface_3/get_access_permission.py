import json
from typing import Any, Dict, Optional, List, Tuple
from tau_bench.envs.tool import Tool


class GetAccessPermission(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        permission_id: Optional[str] = None,
        content_id: Optional[str] = None,
        content_type: Optional[str] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        granted_by: Optional[str] = None,
    ) -> str:
        """
        Retrieve permissions for wiki content with hierarchical support.
        Maps to Confluence permissions table.
        
        Content types use Fibery terminology: 'workspace', 'document'
        (Internally mapped to Confluence: 'space', 'page')
        
        When content_type='document' and content_id is specified,
        returns both direct and inherited permissions from parent documents and workspace.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        # Map Fibery content_type to Confluence DB terminology for internal lookup
        fibery_to_confluence_content_type = {
            "workspace": "space",
            "document": "page",
        }
        
        # Map Confluence DB terminology back to Fibery for output
        confluence_to_fibery_content_type = {
            "space": "workspace",
            "page": "document",
        }
        
        # Validate and convert input content_type if provided
        internal_content_type = None
        if content_type is not None:
            if content_type not in fibery_to_confluence_content_type:
                return json.dumps({
                    "error": f"Invalid content_type. Allowed values: 'workspace', 'document'"
                })
            internal_content_type = fibery_to_confluence_content_type[content_type]

        permissions = data.get("permissions", {})
        pages = data.get("pages", {})
        spaces = data.get("spaces", {})
        
        # Convert content_id to string for consistent comparison
        if content_id is not None:
            content_id = str(content_id)
        
        # Validate content exists if provided
        if content_id and content_type == "document":
            if content_id not in pages:
                return json.dumps({
                    "error": f"Document with ID '{content_id}' not found"
                })
        elif content_id and content_type == "workspace":
            if content_id not in spaces:
                return json.dumps({
                    "error": f"Workspace with ID '{content_id}' not found"
                })

        results = []

        # Helper function to get ancestors of a document
        def get_ancestors(page_id: str) -> List[Tuple[str, str]]:
            """
            Returns list of ancestor (content_type, content_id) pairs.
            Includes immediate parent, grandparent, ..., root document, and workspace.
            """
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
                    # Found a parent document
                    ancestors.append(("page", str(parent_page_id)))
                    current_page_id = str(parent_page_id)
                else:
                    # No parent, add the containing workspace
                    page_space_id = page_data.get("space_id")
                    if page_space_id:
                        ancestors.append(("space", str(page_space_id)))
                    break
            
            return ancestors

        # Determine if we should include inherited permissions
        # Include inherited when: content_type='document' and content_id is specified
        include_inherited = (content_type == "document" and content_id is not None)

        # Helper function to check if operation matches (considering admin encompasses all)
        def operation_matches(perm_operation: str, filter_operation: str) -> bool:
            """
            Check if a permission's operation matches the filter.
            'admin' permission encompasses all other operations.
            """
            if not filter_operation:
                return True
            if perm_operation == filter_operation:
                return True
            # Admin permission covers all operations
            if perm_operation == "admin" and filter_operation in ["view", "edit", "delete", "create", "restrict_other_users"]:
                return True
            return False

        # Case 1: Direct permissions only (workspace or no hierarchy needed)
        if not include_inherited:
            for perm_id, perm_data in permissions.items():
                match = True

                # Apply filters
                if permission_id and perm_id != permission_id:
                    match = False
                if content_id and perm_data.get("content_id") != content_id:
                    match = False
                if internal_content_type and perm_data.get("content_type") != internal_content_type:
                    match = False
                if user_id and perm_data.get("user_id") != user_id:
                    match = False
                if operation and not operation_matches(perm_data.get("operation"), operation):
                    match = False
                if granted_by and perm_data.get("granted_by") != granted_by:
                    match = False

                if match:
                    # Map permission data to Fibery terminology for output
                    result = {
                        "permission_id": perm_id,
                        "content_id": perm_data.get("content_id"),
                        "content_type": confluence_to_fibery_content_type.get(
                            perm_data.get("content_type"),
                            perm_data.get("content_type")
                        ),
                        "user_id": perm_data.get("user_id"),
                        "operation": perm_data.get("operation"),
                        "granted_by": perm_data.get("granted_by"),
                        "granted_at": perm_data.get("granted_at"),
                        "source": "direct",
                        "inherited": False,
                    }
                    results.append(result)

        # Case 2: Include inherited permissions (hierarchical lookup)
        else:
            # Step 1: Get all direct permissions on the document
            for perm_id, perm_data in permissions.items():
                match = True

                # Apply filters (direct permissions only)
                if permission_id and perm_id != permission_id:
                    match = False
                if perm_data.get("content_id") != content_id:
                    match = False
                if perm_data.get("content_type") != "page":
                    match = False
                if user_id and perm_data.get("user_id") != user_id:
                    match = False
                if operation and not operation_matches(perm_data.get("operation"), operation):
                    match = False
                if granted_by and perm_data.get("granted_by") != granted_by:
                    match = False

                if match:
                    result = {
                        "permission_id": perm_id,
                        "content_id": perm_data.get("content_id"),
                        "content_type": "document",  # Fibery term
                        "user_id": perm_data.get("user_id"),
                        "operation": perm_data.get("operation"),
                        "granted_by": perm_data.get("granted_by"),
                        "granted_at": perm_data.get("granted_at"),
                        "source": "direct",
                        "inherited": False,
                        "inheritance_level": 0,
                    }
                    results.append(result)

            # Step 2: Get inherited permissions from ancestor documents and workspace
            ancestors = get_ancestors(content_id)
            
            for level, (ancestor_type, ancestor_id) in enumerate(ancestors, start=1):
                # Find permissions on this ancestor
                for perm_id, perm_data in permissions.items():
                    match = True

                    if perm_data.get("content_id") != ancestor_id:
                        match = False
                    if perm_data.get("content_type") != ancestor_type:
                        match = False
                    if user_id and perm_data.get("user_id") != user_id:
                        match = False
                    if operation and not operation_matches(perm_data.get("operation"), operation):
                        match = False
                    if granted_by and perm_data.get("granted_by") != granted_by:
                        match = False

                    if match:
                        # Map ancestor type to Fibery terminology
                        ancestor_fibery_type = confluence_to_fibery_content_type.get(
                            ancestor_type,
                            ancestor_type
                        )
                        
                        result = {
                            "permission_id": perm_id,
                            "content_id": perm_data.get("content_id"),
                            "content_type": ancestor_fibery_type,
                            "user_id": perm_data.get("user_id"),
                            "operation": perm_data.get("operation"),
                            "granted_by": perm_data.get("granted_by"),
                            "granted_at": perm_data.get("granted_at"),
                            "source": "inherited",
                            "inherited": True,
                            "inherited_from": ancestor_id,
                            "inheritance_level": level,
                        }
                        results.append(result)

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
                "name": "get_access_permission",
                "description": (
                    "Retrieves access permissions for wiki content with hierarchical inheritance support. "
                    "Permissions define what actions specific users can perform on workspaces and documents (view, edit, delete, create, manage access). "
                    "All parameters are optional filters (AND logic) - combine multiple filters to narrow results. "
                    "\n"
                    "Behavior: When content_type='document' and content_id is specified, returns both direct permissions on the document "
                    "AND inherited permissions from parent documents up to the workspace level. "
                    "When querying workspaces or when no document is specified, returns only direct permissions. "
                    "\n"
                    "Inheritance model: Permissions cascade from workspace → parent documents → child documents. "
                    "Results indicate source ('direct' or 'inherited'), inherited_from (ancestor content_id), and inheritance_level (distance from queried document). "
                    "\n"
                    "Content types: 'workspace', 'document' "
                    "Operations: 'view' (read access), 'edit' (modify), 'delete' (remove), 'create' (add new content), 'admin' (full control), 'restrict_other_users' (manage permissions) "
                    "\n"
                    "Use this tool to: audit access control, verify user permissions, find who has specific access, resolve effective permissions, or review permission delegation."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "permission_id": {
                            "type": "string",
                            "description": "ID of the permission to retrieve (optional). When provided, returns only this specific permission.",
                        },
                        "content_id": {
                            "type": "string",
                            "description": (
                                "ID of the workspace or document (optional). "
                                "When content_type='document', includes both direct and inherited permissions from parent documents and workspace. "
                                "When content_type='workspace', returns only direct workspace permissions."
                            ),
                        },
                        "content_type": {
                            "type": "string",
                            "description": (
                                "Type of content to filter by (optional). "
                                "Allowed values: 'workspace', 'document'. "
                                "When 'document', enables hierarchical permission resolution including inherited permissions."
                            )
                        },
                        "user_id": {
                            "type": "string",
                            "description": "ID of the user to filter permissions for (optional). Returns only permissions granted to this user.",
                        },
                        "operation": {
                            "type": "string",
                            "description": (
                                "Type of operation to filter by (optional). "
                                "Allowed values: 'view', 'edit', 'delete', 'create', 'admin', 'restrict_other_users'"
                            )
                        },
                        "granted_by": {
                            "type": "string",
                            "description": "ID of the user who granted the permission (optional). Returns only permissions granted by this user.",
                        },
                    },
                },
            },
        }