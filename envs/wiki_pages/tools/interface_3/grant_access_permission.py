import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool


class GrantAccessPermission(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        content: Dict[str, str],
        operation: str,
        user_id: str,
        granted_by: Optional[str] = None,
    ) -> str:
        """
        Produces (creates) a new permission record to grant access.
        
        Content types use Fibery terminology: 'workspace', 'document'
        (Internally mapped to Confluence: 'space', 'page')
        """
        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            max_id = 0
            for k in table.keys():
                try:
                    max_id = max(max_id, int(k))
                except ValueError:
                    continue
            return str(max_id + 1)

        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not content or not isinstance(content, dict):
            return json.dumps({"error": "Missing required parameter: content must be a JSON object"})

        content_id = content.get("content_id")
        content_type = content.get("content_type")

        if not content_id or not content_type:
            return json.dumps({
                "error": "Missing required parameters: content.content_id and content.content_type are required"
            })

        if not operation:
            return json.dumps({"error": "Missing required parameter: operation is required"})

        if not user_id:
            return json.dumps({"error": "Missing required parameter: user_id is required"})

        # Convert IDs to strings
        content_id = str(content_id)
        user_id = str(user_id)
        if granted_by is not None:
            granted_by = str(granted_by)

        # Map Fibery content_type to Confluence DB terminology for internal storage
        fibery_to_confluence_content_type = {
            "workspace": "space",
            "document": "page",
        }
        
        # Map Confluence DB terminology back to Fibery for output
        confluence_to_fibery_content_type = {
            "space": "workspace",
            "page": "document",
        }

        # Validate content_type (Fibery terminology)
        if content_type not in fibery_to_confluence_content_type:
            return json.dumps({
                "error": f"Invalid content_type. Allowed values: 'workspace', 'document'"
            })

        # Convert to Confluence DB terminology for internal use
        internal_content_type = fibery_to_confluence_content_type[content_type]

        # Validate operation
        allowed_operations = ["view", "edit", "delete", "create", "admin", "restrict_other_users"]
        if operation not in allowed_operations:
            return json.dumps({
                "error": f"Invalid operation. Allowed values: {', '.join(allowed_operations)}"
            })

        # Validate content exists (access Confluence DB tables)
        if internal_content_type == "space":
            spaces = data.get("spaces", {})
            if content_id not in spaces:
                return json.dumps({"error": f"Workspace with ID '{content_id}' not found"})
        elif internal_content_type == "page":
            pages = data.get("pages", {})
            if content_id not in pages:
                return json.dumps({"error": f"Document with ID '{content_id}' not found"})

        # Validate user exists
        users = data.get("users", {})
        if user_id not in users:
            return json.dumps({"error": f"User with ID '{user_id}' not found"})

        # Validate granted_by user exists if provided
        if granted_by is not None:
            users = data.get("users", {})
            if granted_by not in users:
                return json.dumps({"error": f"Granting user with ID '{granted_by}' not found"})

        permissions = data.setdefault("permissions", {})

        # Check for duplicate permission
        for existing in permissions.values():
            if (
                existing.get("content_id") == content_id
                and existing.get("content_type") == internal_content_type
                and existing.get("user_id") == user_id
                and existing.get("operation") == operation
            ):
                return json.dumps({
                    "error": "A permission with the same content_id, content_type, user_id, and operation already exists"
                })

        timestamp = "2025-12-02T12:00:00"
        new_permission_id = generate_id(permissions)

        # Store in Confluence DB format (with internal content_type)
        new_permission_db = {
            "permission_id": new_permission_id,
            "content_id": content_id,
            "content_type": internal_content_type,
            "user_id": user_id,
            "operation": operation,
            "granted_by": granted_by,
            "granted_at": timestamp,
        }

        permissions[new_permission_id] = new_permission_db

        # Return with Fibery terminology
        return json.dumps({
            "permission_id": new_permission_id,
            "content_id": content_id,
            "content_type": content_type,  # Return original Fibery term
            "user_id": user_id,
            "operation": operation,
            "granted_by": granted_by,
            "granted_at": timestamp,
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "grant_access_permission",
                "description": (
                    """Creates a new permission record granting a user specific access rights.
Permissions define what actions a user can perform on wiki content (workspaces and documents).
Permission operations: 'view' (read-only), 'edit' (modify), 'delete' (remove), 'create' (add), 'admin' (full control), 'restrict_other_users' (manage permissions)
Use this tool to: grant access to users, implement access control policies, enable collaboration, or manage workspace/document permissions.
Note: 'admin' permission includes all other permissions. Permissions cascade from parent documents to child documents automatically.
Created permissions apply immediately; removing permissions is done via modify_access_permission."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "object",
                            "description": (
                                "The content to grant permission on (required). "
                                "Must include 'content_id' and 'content_type'."
                            ),
                            "properties": {
                                "content_id": {
                                    "type": "string",
                                    "description": (
                                        "The ID of the content (workspace or document) to grant permission on (required)."
                                    ),
                                },
                                "content_type": {
                                    "type": "string",
                                    "description": (
                                        "The type of content. Allowed values: 'workspace', 'document' (required)."
                                    ),
                                    "enum": ["workspace", "document"],
                                },
                            },
                            "required": ["content_id", "content_type"],
                        },
                        "operation": {
                            "type": "string",
                            "description": (
                                "The operation to grant (required). "
                                "Allowed values: 'view', 'edit', 'delete', 'create', 'admin', 'restrict_other_users'."
                            ),
                        },
                        "user_id": {
                            "type": "string",
                            "description": (
                                "The ID of the user to grant the permission to. The user must exist and be active."
                            ),
                        },
                        "granted_by": {
                            "type": "string",
                            "description": (
                                "The ID of the user granting the permission."
                            ),
                        },
                    },
                    "required": ["content", "operation", "user_id"],
                },
            },
        }