import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class AlterFile(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        file_block_id: str,
        file_name: Optional[str] = None,
        file_url: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Alters an existing file block (attachment) record.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not file_block_id:
            return json.dumps({
                "error": "Missing required parameter: file_block_id is required"
            })

        file_block_id = str(file_block_id)

        # Access Confluence DB (attachments table)
        attachments = data.get("attachments", {})
        if file_block_id not in attachments:
            return json.dumps({"error": f"File block with ID '{file_block_id}' not found"})

        attachment = attachments[file_block_id]

        # Validate status if provided
        if status is not None:
            allowed_statuses = ["current", "archived", "deleted"]
            if status not in allowed_statuses:
                return json.dumps({
                    "error": f"Invalid status. Allowed values: {', '.join(allowed_statuses)}"
                })

        # Update fields if provided
        if file_name is not None:
            attachment["file_name"] = file_name
        if file_url is not None:
            attachment["file_url"] = file_url
        if status is not None:
            attachment["status"] = status

        # Update metadata
        attachment["updated_at"] = "2025-12-02T12:00:00"

        # Map Confluence content_type to Fibery content_type
        content_type_mapping = {
            "page": "document",
            "database": "type",
            "whiteboard": "whiteboard_view",
            "smart_link": "embed_block",
        }
        fibery_content_type = content_type_mapping.get(
            attachment.get("content_type"),
            attachment.get("content_type")
        )

        # Return with Fibery naming
        output_file_block = {
            "file_block_id": attachment.get("attachment_id", file_block_id),
            "content_id": attachment.get("content_id"),
            "content_type": fibery_content_type,
            "host_document_id": attachment.get("host_page_id"),
            "file_name": attachment.get("file_name"),
            "file_url": attachment.get("file_url"),
            "status": attachment.get("status"),
            "uploaded_by": attachment.get("uploaded_by"),
            "uploaded_at": attachment.get("uploaded_at"),
            "updated_at": attachment.get("updated_at"),
        }

        return json.dumps(output_file_block)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "alter_file",
                "description": (
                    """Updates an existing file attachment metadata.
Allows modification of file block properties: file name, file URL (storage location), and status.
Use this tool when you need to rename attachments, update file locations, or change attachment status (archive, delete).
File blocks attach binary files to wiki documents, data types, whiteboards, or embedded resources."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_block_id": {
                            "type": "string",
                            "description": (
                                "The ID of the file block to alter (required)."
                            ),
                        },
                        "file_name": {
                            "type": "string",
                            "description": (
                                "The new file name (optional)."
                            ),
                        },
                        "file_url": {
                            "type": "string",
                            "description": (
                                "The new file URL (optional)."
                            ),
                        },
                        "status": {
                            "type": "string",
                            "description": (
                                "The new status for the file block (optional). "
                                "Allowed values: 'current', 'archived', 'deleted'."
                            ),
                        },
                    },
                    "required": ["file_block_id"],
                },
            },
        }

