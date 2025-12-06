import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class RemoveDocumentVersion(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        paragraph_block_id: str,
        title: Optional[str] = None,
    ) -> str:
        """
        Permanently deletes a document version (paragraph block) record.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not paragraph_block_id:
            return json.dumps({
                "error": "Missing required parameter: paragraph_block_id is required"
            })

        paragraph_block_id = str(paragraph_block_id)

        # Access Confluence DB (page_versions table)
        page_versions = data.get("page_versions", {})
        if paragraph_block_id not in page_versions:
            return json.dumps({
                "error": f"Paragraph block with ID '{paragraph_block_id}' not found"
            })

        # Check if this is the only version for the document
        version = page_versions[paragraph_block_id]
        document_id = version.get("page_id")

        actual_title = version.get("title")

        # Validate confirmation parameters if provided
        if title is not None:
            if title != actual_title:
                return json.dumps({
                    "error": f"Title mismatch. Expected '{actual_title}', got '{title}'. "
                    "Deletion cancelled as safety check - version title does not match provided title."
                })
        
        version_count = sum(
            1 for v in page_versions.values()
            if v.get("page_id") == document_id
        )

        if version_count <= 1:
            return json.dumps({
                "error": f"Cannot delete the only version of document '{document_id}'. "
                "A document must have at least one version."
            })

        # Check if there are any page_version_components referencing this version
        page_version_components = data.get("page_version_components", {})
        for comp in page_version_components.values():
            if comp.get("page_version_id") == paragraph_block_id:
                return json.dumps({
                    "error": f"Cannot delete paragraph block '{paragraph_block_id}' because it has associated components. "
                    "Delete the components first."
                })

        # Remove the version
        deleted_version = page_versions.pop(paragraph_block_id)
        
        # Return with Fibery naming
        output_version = {
            "paragraph_block_id": deleted_version.get("page_version_id", paragraph_block_id),
            "document_id": deleted_version.get("page_id"),
            "version_number": deleted_version.get("version_number"),
            "title": deleted_version.get("title"),
            "body_storage": deleted_version.get("body_storage"),
            "created_at": deleted_version.get("created_at"),
            "_deleted": True,
        }

        return json.dumps(output_version)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "remove_document_version",
                "description": (
                    "Permanently deletes a document version (paragraph block)"
                    "This operation cannot be undone. "
                    "A document must retain at least one version, so the last version cannot be deleted."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "paragraph_block_id": {
                            "type": "string",
                            "description": (
                                "The ID of the paragraph block (document version) to eject (required)."
                            ),
                        },
                        "title": {
                            "type": "string",
                            "description": (
                                "The title of the version being deleted (optional, for confirmation)."
                            )
                        },
                    },
                    "required": ["paragraph_block_id"],
                },
            },
        }
