import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class PublishDocumentVersion(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        document_id: str,
        document_content: Dict[str, Any],
    ) -> str:
        """
        Establishes a new document version (paragraph block) record.
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

        if not document_id:
            return json.dumps({"error": "Missing required parameter: document_id is required"})

        if not document_content or not isinstance(document_content, dict):
            return json.dumps({"error": "Missing required parameter: document_content must be a JSON object"})

        title = document_content.get("title")
        body_storage = document_content.get("body_storage")

        if not title:
            return json.dumps({"error": "Missing required parameter: document_content.title is required"})

        document_id = str(document_id)

        # Validate document exists (access Confluence DB - pages table)
        pages = data.get("pages", {})
        if document_id not in pages:
            return json.dumps({"error": f"Document with ID '{document_id}' not found"})

        # Access Confluence DB (page_versions table)
        page_versions = data.setdefault("page_versions", {})

        # Determine next version number for this document
        existing_versions = [
            v.get("version_number", 0)
            for v in page_versions.values()
            if v.get("page_id") == document_id
        ]
        next_version = max(existing_versions, default=0) + 1

        timestamp = "2025-12-02T12:00:00"
        new_version_id = generate_id(page_versions)

        # Store in Confluence DB format
        new_version_db = {
            "page_version_id": new_version_id,
            "page_id": document_id,
            "version_number": next_version,
            "title": title,
            "body_storage": body_storage,
            "created_at": timestamp,
        }

        page_versions[new_version_id] = new_version_db

        # Return with Fibery naming
        output_version = {
            "paragraph_block_id": new_version_id,
            "document_id": document_id,
            "version_number": next_version,
            "title": title,
            "body_storage": body_storage,
            "created_at": timestamp,
        }

        return json.dumps(output_version)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "publish_document_version",
                "description": (
                    """Creates a new version snapshot of a document, recording its current state.
Version snapshots preserve document content history, enabling rollback, auditing, and change tracking.
The version number is automatically assigned based on existing versions - each new version increments the counter.
Use this tool to: create checkpoints before major edits, establish approved versions, maintain audit trails, or enable version comparison.
Versions capture both document title and content body; manual version creation preserves important states beyond automatic saves.
Useful in workflows where version milestones (draft, review, approved) need to be explicitly marked."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": (
                                "The ID of the document to create a version for (required)."
                            ),
                        },
                        "document_content": {
                            "type": "object",
                            "description": (
                                "The content for the document version (required). "
                                "Must include 'title' (required) and optionally 'body_storage'."
                            ),
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "The title of the document at this version (required).",
                                },
                                "body_storage": {
                                    "type": "string",
                                    "description": "The content body of the document at this version (optional).",
                                },
                            },
                            "required": ["title"],
                        },
                    },
                    "required": ["document_id", "document_content"],
                },
            },
        }

