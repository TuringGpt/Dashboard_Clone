import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteFile(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        file_block_id: str,
        deleted_by: str,
    ) -> str:
        """
        Permanently deletes a file block (attachment) record.
        
        Content types use Fibery terminology: 'document', 'type', 'whiteboard_view', 'embed_block'
        (Internally mapped to Confluence: 'page', 'database', 'whiteboard', 'smart_link')
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not file_block_id or not deleted_by:
            return json.dumps({
                "error": "Missing required parameters: file_block_id and deleted_by are required"
            })

        file_block_id = str(file_block_id)
        deleted_by = str(deleted_by)

        # Validate deleted_by user exists
        users = data.get("users", {})
        if deleted_by not in users:
            return json.dumps({"error": f"User with ID '{deleted_by}' not found"})

        # Access Confluence DB (attachments table)
        attachments = data.get("attachments", {})
        if file_block_id not in attachments:
            return json.dumps({"error": f"File block with ID '{file_block_id}' not found"})

        # Remove from data (hard delete)
        deleted_attachment = attachments.pop(file_block_id)
        
        # Map Confluence DB content_type to Fibery terminology
        confluence_to_fibery_content_type = {
            "page": "document",
            "database": "type",
            "whiteboard": "whiteboard_view",
            "smart_link": "embed_block",
        }
        
        fibery_content_type = confluence_to_fibery_content_type.get(
            deleted_attachment.get("content_type"),
            deleted_attachment.get("content_type")
        )
        
        # Return with Fibery naming
        output_file_block = {
            "file_block_id": deleted_attachment.get("attachment_id", file_block_id),
            "content_id": deleted_attachment.get("content_id"),
            "content_type": fibery_content_type,
            "host_document_id": deleted_attachment.get("host_page_id"),
            "file_name": deleted_attachment.get("file_name"),
            "file_url": deleted_attachment.get("file_url"),
            "status": deleted_attachment.get("status"),
            "uploaded_by": deleted_attachment.get("uploaded_by"),
            "uploaded_at": deleted_attachment.get("uploaded_at"),
            "updated_at": deleted_attachment.get("updated_at"),
            "_deleted": True,
            "_deleted_by": deleted_by,
        }
        return json.dumps(output_file_block)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_file",
                "description": (
                    "Permanently deletes a file block (attachment) from a document, datatype, whiteboard, or embed block. "
                    "This operation performs a hard delete and cannot be reversed or recovered. "
                    "Use this tool to remove uploaded files that are no longer needed or are no longer relevant to the content. "
                    "Ensure you have confirmed the file is truly unwanted before deletion, as recovery is not possible."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_block_id": {
                            "type": "string",
                            "description": (
                                "The ID of the file block to delete (required)."
                            ),
                        },
                        "deleted_by": {
                            "type": "string",
                            "description": (
                                "The user ID of the person performing the deletion (required)."
                            ),
                        },
                    },
                    "required": ["file_block_id", "deleted_by"],
                },
            },
        }