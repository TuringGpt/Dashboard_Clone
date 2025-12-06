import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool


class InsertFile(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        content: Dict[str, str],
        file: Dict[str, str],
        others: Dict[str, Any],
    ) -> str:
        """
        Inserts a new file block (attachment) record.
        
        Content types use Fibery terminology: 'document', 'type', 'whiteboard_view', 'embed_block'
        (Internally mapped to Confluence: 'page', 'database', 'whiteboard', 'smart_link')
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

        # Validate content parameter
        if not content or not isinstance(content, dict):
            return json.dumps({"error": "Missing required parameter: content must be a JSON object"})

        content_id = content.get("content_id")
        content_type = content.get("content_type")

        if not content_id or not content_type:
            return json.dumps({
                "error": "Missing required parameters: content.content_id and content.content_type are required"
            })

        # Validate file parameter
        if not file or not isinstance(file, dict):
            return json.dumps({"error": "Missing required parameter: file must be a JSON object"})

        file_name = file.get("file_name")
        file_url = file.get("file_url")

        if not file_name or not file_url:
            return json.dumps({
                "error": "Missing required parameters: file.file_name and file.file_url are required"
            })

        # Validate others parameter
        if not others or not isinstance(others, dict):
            return json.dumps({"error": "Missing required parameter: others must be a JSON object"})

        uploaded_by = others.get("uploaded_by")
        host_document_id = others.get("host_document_id")
        status = others.get("status", "current")

        if not uploaded_by:
            return json.dumps({"error": "Missing required parameter: others.uploaded_by is required"})

        # Convert IDs to strings
        content_id = str(content_id)
        uploaded_by = str(uploaded_by)
        if host_document_id is not None:
            host_document_id = str(host_document_id)

        # Map Fibery content_type to Confluence DB terminology for internal storage
        fibery_to_confluence_content_type = {
            "document": "page",
            "type": "database",
            "whiteboard_view": "whiteboard",
            "embed_block": "smart_link",
        }
        
        # Map Confluence DB terminology back to Fibery for output
        confluence_to_fibery_content_type = {
            "page": "document",
            "database": "type",
            "whiteboard": "whiteboard_view",
            "smart_link": "embed_block",
        }

        # Validate content_type (Fibery terminology)
        if content_type not in fibery_to_confluence_content_type:
            return json.dumps({
                "error": f"Invalid content_type. Allowed values: 'document', 'type', 'whiteboard_view', 'embed_block'"
            })

        # Convert to Confluence DB terminology for internal use
        internal_content_type = fibery_to_confluence_content_type[content_type]

        # Validate status
        allowed_statuses = ["current", "archived", "deleted"]
        if status not in allowed_statuses:
            return json.dumps({
                "error": f"Invalid status. Allowed values: {', '.join(allowed_statuses)}"
            })

        # Validate content exists based on content_type (access Confluence DB)
        if internal_content_type == "page":
            pages = data.get("pages", {})
            if content_id not in pages:
                return json.dumps({"error": f"Document with ID '{content_id}' not found"})
        elif internal_content_type == "database":
            databases = data.get("databases", {})
            if content_id not in databases:
                return json.dumps({"error": f"Type with ID '{content_id}' not found"})
        elif internal_content_type == "whiteboard":
            whiteboards = data.get("whiteboards", {})
            if content_id not in whiteboards:
                return json.dumps({"error": f"Whiteboard view with ID '{content_id}' not found"})
        elif internal_content_type == "smart_link":
            smart_links = data.get("smart_links", {})
            if content_id not in smart_links:
                return json.dumps({"error": f"Embed block with ID '{content_id}' not found"})

        # Validate host_document_id exists if provided
        if host_document_id is not None:
            pages = data.get("pages", {})
            if host_document_id not in pages:
                return json.dumps({"error": f"Host document with ID '{host_document_id}' not found"})

        # Validate uploader exists
        users = data.get("users", {})
        if uploaded_by not in users:
            return json.dumps({"error": f"User with ID '{uploaded_by}' not found"})

        # Access Confluence DB (attachments table)
        attachments = data.setdefault("attachments", {})

        timestamp = "2025-12-02T12:00:00"
        new_file_block_id = generate_id(attachments)

        # Store in Confluence DB format (with internal content_type)
        new_attachment_db = {
            "attachment_id": new_file_block_id,
            "content_id": content_id,
            "content_type": internal_content_type,
            "host_page_id": host_document_id,
            "file_name": file_name,
            "file_url": file_url,
            "status": status,
            "uploaded_by": uploaded_by,
            "uploaded_at": timestamp,
            "updated_at": timestamp,
        }

        attachments[new_file_block_id] = new_attachment_db

        # Return with Fibery naming and terminology
        output_file_block = {
            "file_block_id": new_file_block_id,
            "content_id": content_id,
            "content_type": content_type,  # Return original Fibery term
            "host_document_id": host_document_id,
            "file_name": file_name,
            "file_url": file_url,
            "status": status,
            "uploaded_by": uploaded_by,
            "uploaded_at": timestamp,
            "updated_at": timestamp,
        }

        return json.dumps(output_file_block)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "insert_file",
                "description": (
                    "Inserts a new file block (attachment). "
                    """Uploads and attaches a new file to wiki content.
File blocks are binary attachments associated with documents, datatypes, whiteboards, or embed blocks.
Supported content types: 'document', 'type' (datatype), 'whiteboard_view', 'embed_block'
Files are stored at the provided file_url and associated with the specified content.
Optional host_document_id allows specifying where the file reference appears within a document.
Use this tool to attach supporting materials, datasets, archives, or other files to wiki content.
Note: Actual file upload to storage backend should be handled before calling this tool."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "object",
                            "description": (
                                "The content this file is associated with (required). "
                                "Must include 'content_id' and 'content_type'."
                            ),
                            "properties": {
                                "content_id": {
                                    "type": "string",
                                    "description": (
                                        "The ID of the content this file is associated with (required)."
                                    ),
                                },
                                "content_type": {
                                    "type": "string",
                                    "description": (
                                        "The type of content. Allowed values: 'document', 'type', 'whiteboard_view', 'embed_block' (required)."
                                    ),
                                    "enum": ["document", "type", "whiteboard_view", "embed_block"],
                                },
                            },
                            "required": ["content_id", "content_type"],
                        },
                        "file": {
                            "type": "object",
                            "description": (
                                "The file information (required). "
                                "Must include 'file_name' and 'file_url'."
                            ),
                            "properties": {
                                "file_name": {
                                    "type": "string",
                                    "description": "The name of the file (required).",
                                },
                                "file_url": {
                                    "type": "string",
                                    "description": "The URL where the file is stored (required).",
                                },
                            },
                            "required": ["file_name", "file_url"],
                        },
                        "others": {
                            "type": "object",
                            "description": (
                                "Other parameters (required). "
                                "Must include 'uploaded_by'. Optional: 'host_document_id', 'status'."
                            ),
                            "properties": {
                                "uploaded_by": {
                                    "type": "string",
                                    "description": "The user ID of the uploader (required).",
                                },
                                "host_document_id": {
                                    "type": "string",
                                    "description": (
                                        "The ID of the document where the file block is displayed (optional)."
                                    ),
                                },
                                "status": {
                                    "type": "string",
                                    "description": (
                                        "The status of the file block. Allowed values: 'current', 'archived', 'deleted'. Defaults to 'current'."
                                    ),
                                    "enum": ["current", "archived", "deleted"],
                                },
                            },
                            "required": ["uploaded_by"],
                        },
                    },
                    "required": ["content", "file", "others"],
                },
            },
        }