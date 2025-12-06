import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class EstablishAttachment(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        page_id: str,
        file_name: str,
        file_content: Dict[str, Any],
        uploaded_by: str
    ) -> str:
        """
        Establish (create) an attachment on a page.
        
        Args:
            data: Environment data
            page_id: Page ID where attachment will be added (required)
            file_name: Name of the file (required)
            file_content: Content of the file (required)
            uploaded_by: User ID who uploaded the file (required)
        """
        def generate_id(table: Dict[str, Any]) -> str:
            """Generate a new unique ID for a record."""
            if not table:
                return "1"
            try:
                return str(max(int(k) for k in table.keys()) + 1)
            except ValueError:
                return "1"
        
        # Validate required fields
        if not page_id or not file_name or not uploaded_by or not file_content:
            return json.dumps({
                "error": "page_id, file_name, file_content and uploaded_by are required parameters"
            })
        
        # Get tables
        attachments = data.get("attachments", {})
        users = data.get("users", {})
        pages = data.get("pages", {})

        # Validate file_content structure
        required_fc_fields = ["content_id", "content_type", "file_url"]
        missing = [f for f in required_fc_fields if f not in file_content]
        if missing:
            return json.dumps({
                "error": f"file_content is missing required fields: {', '.join(missing)}"
            })
        
        # Validate content_type value
        valid_content_types = ["page", "database", "whiteboard", "smart_link"]
        if file_content["content_type"] not in valid_content_types:
            return json.dumps({
                "error": f"Invalid content_type '{file_content['content_type']}'. "
                         f"Must be one of: {', '.join(valid_content_types)}"
            })
        
        # Validate uploaded_by user exists
        if uploaded_by not in users:
            return json.dumps({
                "error": f"User with ID {uploaded_by} not found"
            })
        
        user = users.get(uploaded_by, {})
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID {uploaded_by} is not active"
            })
        
        # Validate page exists
        if page_id not in pages:
            return json.dumps({
                "error": f"Page with ID {page_id} not found"
            })
        
        # Generate new attachment ID
        attachment_id = generate_id(attachments)
        
        # Create attachment record
        attachment = {
            "attachment_id": attachment_id,
            "content_id": file_content["content_id"],
            "content_type": file_content["content_type"],
            "host_page_id": page_id,
            "file_name": file_name,
            "file_url": file_content["file_url"],
            "status": "current",
            "uploaded_by": uploaded_by,
            "uploaded_at": "2025-12-02T12:00:00",
            "updated_at": "2025-12-02T12:00:00"
        }
        
        # Add to data
        attachments[attachment_id] = attachment
        
        return json.dumps(attachment)
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "establish_attachment",
                "description": "Establish (create) an attachment on a page. Requires page_id, file_name, file_content, and uploaded_by.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "Page ID where attachment will be added"
                        },
                        "file_name": {
                            "type": "string",
                            "description": "Name of the file"
                        },
                        "file_content": {
                            "type": "object",
                            "description": "An object containing content_id, content_type, and file_url",
                            "properties": {
                                "content_id": {
                                    "type": "string",
                                    "description": "ID of content"

                                },
                                "content_type": {
                                    "type": "string",
                                    "description": "Type of content: 'page', 'database', 'whiteboard', 'smart_link'"
                                },
                                "file_url": {
                                    "type": "string",
                                    "description": "URL of the file"
                                }
                            },
                            "required": ["content_id", "content_type", "file_url"]
                        },
                        "uploaded_by": {
                            "type": "string",
                            "description": "User ID who uploaded the file"
                        }
                    },
                    "required": ["page_id", "file_name", "file_content", "uploaded_by"]
                }
            }
        }
