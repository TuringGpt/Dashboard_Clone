import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool


class InsertDatatype(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        title: str,
        created_by: str,
        host_workspace_id: Optional[str] = None,
        host_document_id: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "current",
    ) -> str:
        """
        Create a new datatype (database) in Fibery.
        Datatypes are structured data containers that can be hosted at workspace or document level.
        
        Maps to Confluence databases table.
        
        Args:
            title: Title of the datatype (required)
            created_by: User ID of the creator (required)
            host_workspace_id: ID of the workspace hosting this datatype (optional, mutually exclusive with host_document_id)
            host_document_id: ID of the document hosting this datatype (optional, mutually exclusive with host_workspace_id)
            description: Description of the datatype (optional)
            status: Datatype status, defaults to 'current' (optional)
        """

        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)

        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        # Validate required parameters
        if not title or not created_by:
            return json.dumps({
                "error": "Missing required parameters: title and created_by are required"
            })

        # Validate that either host_workspace_id OR host_document_id is provided (mutually exclusive)
        if not host_workspace_id and not host_document_id:
            return json.dumps({
                "error": "Either host_workspace_id or host_document_id must be provided"
            })

        if host_workspace_id and host_document_id:
            return json.dumps({
                "error": "Only one of host_workspace_id or host_document_id should be provided"
            })

        # Convert IDs to strings
        created_by = str(created_by)
        if host_workspace_id is not None:
            host_workspace_id = str(host_workspace_id)
        if host_document_id is not None:
            host_document_id = str(host_document_id)

        # Validate status
        allowed_statuses = ["current", "archived", "deleted"]
        if status not in allowed_statuses:
            return json.dumps({
                "error": f"Invalid status. Allowed values: {', '.join(allowed_statuses)}"
            })

        # Validate host workspace if provided
        spaces = data.get("spaces", {})
        if host_workspace_id:
            if host_workspace_id not in spaces:
                return json.dumps({
                    "error": f"Workspace with ID '{host_workspace_id}' not found"
                })

        # Validate host document if provided
        pages = data.get("pages", {})
        if host_document_id:
            if host_document_id not in pages:
                return json.dumps({
                    "error": f"Document with ID '{host_document_id}' not found"
                })

        # Validate creator exists and is active
        users = data.get("users", {})
        if created_by not in users:
            return json.dumps({
                "error": f"User with ID '{created_by}' not found"
            })

        user = users[created_by]
        if user.get("status") != "active":
            return json.dumps({
                "error": f"User with ID '{created_by}' is not active"
            })

        # Validate "create" permission on host
        permissions = data.get("permissions", {})
        
        # Check if user has create permission on host workspace or document
        has_create_permission = False
        
        if host_workspace_id:
            # Check for create permission on workspace
            for perm in permissions.values():
                if (perm.get("content_id") == host_workspace_id
                    and perm.get("content_type") == "space"
                    and perm.get("user_id") == created_by
                    and perm.get("operation") == "create"):
                    has_create_permission = True
                    break
        elif host_document_id:
            # Check for create permission on document
            for perm in permissions.values():
                if (perm.get("content_id") == host_document_id
                    and perm.get("content_type") == "page"
                    and perm.get("user_id") == created_by
                    and perm.get("operation") == "create"):
                    has_create_permission = True
                    break
        
        if not has_create_permission:
            return json.dumps({
                "error": f"User with ID '{created_by}' does not have 'create' permission on the host"
            })

        # Check for duplicate title at the same host level
        databases = data.get("databases", {})
        for existing_db in databases.values():
            if (existing_db.get("title") == title
                and existing_db.get("host_space_id") == host_workspace_id
                and existing_db.get("host_page_id") == host_document_id):
                return json.dumps({
                    "error": f"Datatype with title '{title}' already exists at this host level"
                })

        # Generate new datatype ID
        new_type_id = generate_id(databases)

        timestamp = "2025-12-02T12:00:00"

        # Create new datatype (database) - stored in Confluence DB format internally
        new_database = {
            "database_id": new_type_id,
            "title": title,
            "description": description,
            "host_space_id": host_workspace_id,
            "host_page_id": host_document_id,
            "status": status,
            "created_by": created_by,
            "created_at": timestamp,
            "updated_by": created_by,
            "updated_at": timestamp,
        }

        databases[new_type_id] = new_database

        # Return with Fibery terminology - no internal Confluence DB fields exposed
        return json.dumps({
            "success": True,
            "type_id": new_type_id,
            "type": {
                "type_id": new_type_id,
                "title": title,
                "description": description,
                "host_workspace_id": host_workspace_id,
                "host_document_id": host_document_id,
                "status": status,
                "created_by": created_by,
                "created_at": timestamp,
                "updated_by": created_by,
                "updated_at": timestamp,
            }
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "insert_datatype",
                "description": (
                    "Creates a new datatype (database). "
                    "Datatypes are structured data containers that can be hosted at workspace level "
                    "or embedded within a document. "
                    "Either host_workspace_id or host_document_id must be provided (mutually exclusive). "
                    "The creator must be an active user with 'create' permission on the host."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": (
                                "Title of the datatype. "
                                "Must be unique at the same host level."
                            ),
                        },
                        "created_by": {
                            "type": "string",
                            "description": (
                                "User ID of the datatype creator. "
                                "The user must exist, be active, and have 'create' permission on the host."
                            ),
                        },
                        "host_workspace_id": {
                            "type": "string",
                            "description": (
                                "ID of the workspace hosting this datatype (optional). "
                                "Mutually exclusive with host_document_id. "
                                "The workspace must exist."
                            ),
                        },
                        "host_document_id": {
                            "type": "string",
                            "description": (
                                "ID of the document hosting this datatype (optional). "
                                "Mutually exclusive with host_workspace_id. "
                                "The document must exist."
                            ),
                        },
                        "description": {
                            "type": "string",
                            "description": (
                                "Description of the datatype (optional)."
                            ),
                        },
                        "status": {
                            "type": "string",
                            "description": (
                                "Datatype status. Defaults to 'current'. "
                                "Allowed values: 'current', 'archived', 'deleted'."
                            ),
                            "enum": ["current", "archived", "deleted"],
                        },
                    },
                    "required": ["title", "created_by"],
                },
            },
        }