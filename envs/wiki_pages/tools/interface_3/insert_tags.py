import json
from typing import Any, Dict, List
from tau_bench.envs.tool import Tool

class InsertTags(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        tags: List[Dict[str, str]],
    ) -> str:
        """
        Inserts multiple new tags (page labels) records.
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

        if not tags or not isinstance(tags, list):
            return json.dumps({"error": "Missing required parameter: tags must be an array"})

        if len(tags) == 0:
            return json.dumps({"error": "tags array cannot be empty"})

        # Validate each tag in the array
        for i, tag in enumerate(tags):
            if not isinstance(tag, dict):
                return json.dumps({"error": f"tags[{i}] must be a JSON object"})
            
            if not tag.get("document_id"):
                return json.dumps({"error": f"tags[{i}].document_id is required"})
            if not tag.get("tag_name"):
                return json.dumps({"error": f"tags[{i}].tag_name is required"})
            if not tag.get("added_by"):
                return json.dumps({"error": f"tags[{i}].added_by is required"})

        pages = data.get("pages", {})
        users = data.get("users", {})
        page_labels = data.setdefault("page_labels", {})

        results = []
        errors = []

        for i, tag in enumerate(tags):
            document_id = str(tag.get("document_id"))
            tag_name = tag.get("tag_name")
            added_by = str(tag.get("added_by"))

            # Validate document exists
            if document_id not in pages:
                errors.append(f"tags[{i}]: Document with ID '{document_id}' not found")
                continue

            # Validate added_by user exists
            if added_by not in users:
                errors.append(f"tags[{i}]: User with ID '{added_by}' not found")
                continue

            # Check for duplicate (document_id, tag_name) combination
            duplicate_found = False
            for existing in page_labels.values():
                if (
                    existing.get("page_id") == document_id
                    and existing.get("label_name") == tag_name
                ):
                    errors.append(f"tags[{i}]: Tag '{tag_name}' already exists on document '{document_id}'")
                    duplicate_found = True
                    break

            if duplicate_found:
                continue

            timestamp = "2025-12-02T12:00:00"
            new_tag_id = generate_id(page_labels)

            # Store in Confluence DB format
            new_label_db = {
                "page_label_id": new_tag_id,
                "page_id": document_id,
                "label_name": tag_name,
                "added_by": added_by,
                "added_at": timestamp,
            }

            page_labels[new_tag_id] = new_label_db

            # Return with Fibery naming
            output_tag = {
                "tag_id": new_tag_id,
                "document_id": document_id,
                "tag_name": tag_name,
                "added_by": added_by,
                "added_at": timestamp,
            }
            results.append(output_tag)

        response = {
            "entity_type": "tags",
            "inserted_count": len(results),
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
                "name": "insert_tags",
                "description": (
                    "Inserts multiple new tags (labels) on documents"
                    "Tags are used to categorize and organize documents for easier discovery and filtering. "
                    "Each document can have multiple tags, but a specific tag can only be added to a document once."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "array",
                            "description": (
                                "Array of tag objects to insert (required). "
                                "Each object must include 'document_id', 'tag_name', and 'added_by'."
                            ),
                            "items": {
                                "type": "object",
                                "properties": {
                                    "document_id": {
                                        "type": "string",
                                        "description": "The ID of the document to add the tag to (required).",
                                    },
                                    "tag_name": {
                                        "type": "string",
                                        "description": "The name of the tag to add (required).",
                                    },
                                    "added_by": {
                                        "type": "string",
                                        "description": "The user ID of the person adding the tag (required).",
                                    },
                                },
                                "required": ["document_id", "tag_name", "added_by"],
                            },
                        },
                    },
                    "required": ["tags"],
                },
            },
        }

