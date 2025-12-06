import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class DiscardTag(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        fields: Dict[str, Any],
    ) -> str:
        """
        Permanently deletes a tag (page label) record.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not fields or not isinstance(fields, dict):
            return json.dumps({"error": "Missing required parameter: fields must be a JSON object"})

        tag_id = fields.get("tag_id")
        tag_name: Optional[str] = fields.get("tag_name")

        if not tag_id:
            return json.dumps({
                "error": "Missing required parameter: fields.tag_id is required"
            })

        tag_id = str(tag_id)

        # Access Confluence DB (page_labels table)
        page_labels = data.get("page_labels", {})
        if tag_id not in page_labels:
            return json.dumps({"error": f"Tag with ID '{tag_id}' not found"})

        page_label = page_labels[tag_id]

        # Optional: verify tag_name matches if provided
        if tag_name is not None and page_label.get("label_name") != tag_name:
            return json.dumps({
                "error": f"Tag name mismatch. Expected '{page_label.get('label_name')}', got '{tag_name}'"
            })

        # Remove from data
        deleted_label = page_labels.pop(tag_id)
        
        # Return with Fibery naming
        output_tag = {
            "tag_id": deleted_label.get("page_label_id", tag_id),
            "document_id": deleted_label.get("page_id"),
            "tag_name": deleted_label.get("label_name"),
            "added_by": deleted_label.get("added_by"),
            "added_at": deleted_label.get("added_at"),
            "_deleted": True,
        }

        return json.dumps(output_tag)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "discard_tag",
                "description": (
                    """Permanently removes a tag (categorization label) from a document.
This operation performs a hard delete and cannot be reversed.
Use this tool to remove inappropriate, obsolete, or incorrect labels from documents.
Tags are organizational labels used for categorization and discovery - removing a tag does not affect the document itself, only its categorization.
Use discard_tag to remove individual tags or alter_tags to modify tag properties (names, attribution)."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "description": (
                                "The fields for the delete operation (required). "
                                "Must include 'tag_id'. Optional: 'tag_name' for verification."
                            ),
                            "properties": {
                                "tag_id": {
                                    "type": "string",
                                    "description": "The ID of the tag to eject (required).",
                                },
                                "tag_name": {
                                    "type": "string",
                                    "description": "The tag name for verification (optional). If provided, deletion will fail if it doesn't match.",
                                },
                            },
                            "required": ["tag_id"],
                        },
                    },
                    "required": ["fields"],
                },
            },
        }
