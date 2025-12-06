import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteAttachment(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        page_id: str,
        attachment_id: str,
        deleted_by: str
    ) -> str:
        """
        Delete an attachment from a page.
        
        Args:
            data: Environment data
            page_id: Page ID where attachment exists (required)
            attachment_id: ID of the attachment to delete (required)
            deleted_by: User ID who is deleting the attachment (required)
        """
        # Validate required fields
        if not page_id or not attachment_id or not deleted_by:
            return json.dumps({
                "error": "page_id, attachment_id, and deleted_by are required parameters"
            })
        
        # Get tables
        attachments = data.get("attachments", {})
        users = data.get("users", {})
        pages = data.get("pages", {})
        
        # Validate deleted_by user exists
        if deleted_by not in users:
            return json.dumps({
                "error": f"User with ID {deleted_by} not found"
            })
        
        user = users.get(deleted_by, {})
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID {deleted_by} is not active"
            })
        
        # Validate page exists
        if page_id not in pages:
            return json.dumps({
                "error": f"Page with ID {page_id} not found"
            })
        
        # Validate attachment exists
        if attachment_id not in attachments:
            return json.dumps({
                "error": f"Attachment with ID {attachment_id} not found"
            })
        
        attachment = attachments[attachment_id]
        
        # Validate attachment belongs to the specified page
        if attachment.get("content_id") != page_id or attachment.get("host_page_id") != page_id:
            return json.dumps({
                "error": f"Attachment {attachment_id} does not belong to page {page_id}"
            })
        
        # Check if already deleted
        if attachment.get("status") == "deleted":
            return json.dumps({
                "error": f"Attachment with ID {attachment_id} is already deleted"
            })
        
        # Update status to deleted (soft delete)
        attachment = attachment.copy()
        attachment["status"] = "deleted"
        attachment["updated_at"] = "2025-12-02T12:00:00"
        
        # Save back to data
        attachments[attachment_id] = attachment
        
        return json.dumps({
            "page_id": page_id,
            "attachment_id": attachment_id,
            "deleted_by": deleted_by,
            "status": "deleted"
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_attachment",
                "description": "Delete an attachment from a page by changing its status to 'deleted'. Requires page_id, attachment_id, and deleted_by.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "Page ID where attachment exists"
                        },
                        "attachment_id": {
                            "type": "string",
                            "description": "ID of the attachment to delete"
                        },
                        "deleted_by": {
                            "type": "string",
                            "description": "User ID who is deleting the attachment"
                        }
                    },
                    "required": ["page_id", "attachment_id", "deleted_by"]
                }
            }
        }
