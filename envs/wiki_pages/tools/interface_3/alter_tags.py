import json
from typing import Any, Dict, List, Optional
from tau_bench.envs.tool import Tool

class AlterTags(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        tags: List[Dict[str, Any]],
    ) -> str:
        """
        Alters multiple existing tag (page label) records.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not tags or not isinstance(tags, list):
            return json.dumps({"error": "Missing required parameter: tags must be an array"})

        if len(tags) == 0:
            return json.dumps({"error": "tags array cannot be empty"})

        # Validate each tag in the array
        for i, tag in enumerate(tags):
            if not isinstance(tag, dict):
                return json.dumps({"error": f"tags[{i}] must be a JSON object"})
            
            if not tag.get("tag_id"):
                return json.dumps({"error": f"tags[{i}].tag_id is required"})

        page_labels = data.get("page_labels", {})
        users = data.get("users", {})

        results = []
        errors = []

        for i, tag in enumerate(tags):
            tag_id = str(tag.get("tag_id"))
            tag_name: Optional[str] = tag.get("tag_name")
            added_by: Optional[str] = tag.get("added_by")

            # Validate tag exists
            if tag_id not in page_labels:
                errors.append(f"tags[{i}]: Tag with ID '{tag_id}' not found")
                continue

            page_label = page_labels[tag_id]
            document_id = page_label.get("page_id")

            # Validate added_by user exists if provided
            if added_by is not None:
                added_by = str(added_by)
                if added_by not in users:
                    errors.append(f"tags[{i}]: User with ID '{added_by}' not found")
                    continue

            # Check for duplicate (document_id, tag_name) if tag_name is being changed
            if tag_name is not None and tag_name != page_label.get("label_name"):
                duplicate_found = False
                for lid, existing in page_labels.items():
                    if (
                        lid != tag_id
                        and existing.get("page_id") == document_id
                        and existing.get("label_name") == tag_name
                    ):
                        errors.append(f"tags[{i}]: Tag '{tag_name}' already exists on document '{document_id}'")
                        duplicate_found = True
                        break

                if duplicate_found:
                    continue

            # Update fields if provided
            if tag_name is not None:
                page_label["label_name"] = tag_name
            if added_by is not None:
                page_label["added_by"] = added_by

            # Update timestamp
            page_label["added_at"] = "2025-12-02T12:00:00"

            # Return with Fibery naming
            output_tag = {
                "tag_id": page_label.get("page_label_id", tag_id),
                "document_id": page_label.get("page_id"),
                "tag_name": page_label.get("label_name"),
                "added_by": page_label.get("added_by"),
                "added_at": page_label.get("added_at"),
            }
            results.append(output_tag)

        response = {
            "entity_type": "tags",
            "altered_count": len(results),
            "results": results,
        }

        if errors:
            response["errors"] = errors

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "alter_tags",
                "description": (
                    """Updates properties of multiple tags (document labels) in batch.
Allows modification of tag properties: tag name and the user attribution (who added the tag).
Use this tool to rename tags across documents, correct tag names, or update tag ownership history.
Tags are categorization labels applied to documents for organization, filtering, and discovery purposes.
This tool performs batch updates and reports both successful changes and any errors encountered."""
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "array",
                            "description": (
                                "Array of tag objects to alter (required). "
                                "Each object must include 'tag_id'. Optional: 'tag_name', 'added_by'."
                            ),
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tag_id": {
                                        "type": "string",
                                        "description": "The ID of the tag to alter (required).",
                                    },
                                    "tag_name": {
                                        "type": "string",
                                        "description": "The new tag name (optional). Must be unique for the document.",
                                    },
                                    "added_by": {
                                        "type": "string",
                                        "description": "The new user ID for who added the tag (optional).",
                                    },
                                },
                                "required": ["tag_id"],
                            },
                        },
                    },
                    "required": ["tags"],
                },
            },
        }

