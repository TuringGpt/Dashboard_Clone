import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class RetrieveEntityByType(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generic retrieval for embed blocks, file blocks, or tags.
        
        Content types use Fibery terminology: 'document', 'type', 'whiteboard_view', 'embed_block'
        (Internally mapped to Confluence: 'page', 'database', 'whiteboard', 'smart_link')
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not entity_type:
            return json.dumps({"error": "Missing required parameter: entity_type is required"})

        # Map Fibery entity types to Confluence DB tables
        entity_type_mapping = {
            "embed_blocks": "smart_links",
            "file_blocks": "attachments",
            "tags": "page_labels",
        }

        allowed_entity_types = list(entity_type_mapping.keys())
        if entity_type not in allowed_entity_types:
            return json.dumps({
                "error": f"Invalid entity_type. Allowed values: {', '.join(allowed_entity_types)}"
            })

        if filters is not None and not isinstance(filters, dict):
            return json.dumps({"error": "filters must be a JSON object if provided"})

        # Get the corresponding DB table name
        db_table_name = entity_type_mapping[entity_type]
        table = data.get(db_table_name, {})
        results = []
        effective_filters = filters or {}

        # Field mappings from Fibery to Confluence DB for each entity type
        field_mappings = {
            "embed_blocks": {
                "embed_block_id": "smart_link_id",
                "host_document_id": "host_page_id",
            },
            "file_blocks": {
                "file_block_id": "attachment_id",
                "host_document_id": "host_page_id",
                "content_type": "content_type",  # Will be mapped after retrieval
            },
            "tags": {
                "tag_id": "page_label_id",
                "document_id": "page_id",
                "tag_name": "label_name",
            },
        }

        # Reverse mappings for output (Confluence DB to Fibery)
        output_mappings = {
            "embed_blocks": {
                "smart_link_id": "embed_block_id",
                "host_page_id": "host_document_id",
            },
            "file_blocks": {
                "attachment_id": "file_block_id",
                "host_page_id": "host_document_id",
            },
            "tags": {
                "page_label_id": "tag_id",
                "page_id": "document_id",
                "label_name": "tag_name",
            },
        }

        # Confluence to Fibery content_type mapping (for file_blocks)
        confluence_to_fibery_content_type = {
            "page": "document",
            "database": "type",
            "whiteboard": "whiteboard_view",
            "smart_link": "embed_block",
        }
        
        # Fibery to Confluence content_type mapping (for filtering)
        fibery_to_confluence_content_type = {
            "document": "page",
            "type": "database",
            "whiteboard_view": "whiteboard",
            "embed_block": "smart_link",
        }

        # Convert filter keys from Fibery to Confluence naming
        mapping = field_mappings.get(entity_type, {})
        mapped_filters = {}
        for key, value in effective_filters.items():
            mapped_key = mapping.get(key, key)
            
            # Special handling: convert content_type filter from Fibery to Confluence
            if entity_type == "file_blocks" and key == "content_type":
                if value in fibery_to_confluence_content_type:
                    mapped_filters[mapped_key] = fibery_to_confluence_content_type[value]
                else:
                    mapped_filters[mapped_key] = value
            else:
                mapped_filters[mapped_key] = value

        # Get ID field for this entity type
        id_field_mapping = {
            "embed_blocks": "smart_link_id",
            "file_blocks": "attachment_id",
            "tags": "page_label_id",
        }
        id_field = id_field_mapping[entity_type]

        for record_id, record in table.items():
            if not isinstance(record, dict):
                continue

            match = True
            for key, value in mapped_filters.items():
                if key == id_field:
                    stored_id = record.get(id_field)
                    if str(record_id) != str(value) and str(stored_id) != str(value):
                        match = False
                        break
                else:
                    if record.get(key) != value:
                        match = False
                        break

            if match:
                # Map output to Fibery naming
                result_record = {}
                output_mapping = output_mappings.get(entity_type, {})
                
                for db_key, db_value in record.items():
                    fibery_key = output_mapping.get(db_key, db_key)
                    
                    # Special handling: convert content_type from Confluence to Fibery
                    if entity_type == "file_blocks" and db_key == "content_type":
                        result_record[fibery_key] = confluence_to_fibery_content_type.get(
                            db_value,
                            db_value
                        )
                    else:
                        result_record[fibery_key] = db_value
                
                # Ensure ID field is present
                fibery_id_field = list(field_mappings[entity_type].keys())[0]
                if fibery_id_field not in result_record:
                    result_record[fibery_id_field] = str(record_id)
                
                results.append(result_record)

        return json.dumps({
            "entity_type": entity_type,
            "count": len(results),
            "results": results,
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "retrieve_entity_by_type",
                "description": (
                    "Retrieves entities by type with flexible filtering. "
                    "Supports three entity types: 'embed_blocks' (smart links to internal/external content), "
                    "'file_blocks' (file attachments), 'tags' (document categorization labels). "
                    "Each entity type supports different filters - see parameter documentation for supported filters. "
                    "For file_blocks, content_type filters use Fibery terminology (document, type, whiteboard_view, embed_block). "
                    "Use this tool to: find embedded resources by criteria, locate file attachments, query tags across documents, audit references, or discover tag usage."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "The type of entity to retrieve (required). Allowed values: 'embed_blocks' (smart links to internal/external content), 'file_blocks' (file attachments), 'tags' (document categorization labels).",
                        },
                        "filters": {
                            "type": "object",
                            "description": (
                                "Optional JSON object with filter key-value pairs (AND logic). "
                                "embed_blocks: embed_block_id, title, url, target_id, target_type, host_document_id, created_by, updated_by. "
                                "file_blocks: file_block_id, content_id, content_type, host_document_id, file_name, status, uploaded_by. "
                                "tags: tag_id, document_id, tag_name, added_by. "
                                "content_type enum: 'document', 'type', 'whiteboard_view', 'embed_block'."
                            ),
                            "properties": {
                                "embed_block_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the embed block (e.g., '1', '50'). Use with entity_type='embed_blocks'.",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "The exact title of the entity to filter by.",
                                },
                                "url": {
                                    "type": "string",
                                    "description": "The URL of the embed block (e.g., 'https://example.com'). Use with entity_type='embed_blocks'.",
                                },
                                "target_id": {
                                    "type": "string",
                                    "description": "The ID of the target entity referenced by the embed block (e.g., '10'). Use with entity_type='embed_blocks'.",
                                },
                                "target_type": {
                                    "type": "string",
                                    "description": "The type of target referenced by the embed block. Use with entity_type='embed_blocks'.",
                                },
                                "host_document_id": {
                                    "type": "string",
                                    "description": "The ID of the document hosting the entity (e.g., '5'). Use with entity_type='embed_blocks' or 'file_blocks'.",
                                },
                                "created_by": {
                                    "type": "string",
                                    "description": "The user_id of the creator (e.g., '12'). Use with entity_type='embed_blocks'.",
                                },
                                "updated_by": {
                                    "type": "string",
                                    "description": "The user_id of the last updater (e.g., '8'). Use with entity_type='embed_blocks'.",
                                },
                                "file_block_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the file block (e.g., '1', '25'). Use with entity_type='file_blocks'.",
                                },
                                "content_id": {
                                    "type": "string",
                                    "description": "The content ID associated with the file (e.g., '10'). Use with entity_type='file_blocks'.",
                                },
                                "content_type": {
                                    "type": "string",
                                    "description": "The type of content the file is attached to. Allowed values: 'document', 'type', 'whiteboard_view', 'embed_block'. Use with entity_type='file_blocks'.",
                                },
                                "file_name": {
                                    "type": "string",
                                    "description": "The exact file name to filter by (e.g., 'report.pdf'). Use with entity_type='file_blocks'.",
                                },
                                "status": {
                                    "type": "string",
                                    "description": "The status of the file. Use with entity_type='file_blocks'.",
                                },
                                "uploaded_by": {
                                    "type": "string",
                                    "description": "The user_id who uploaded the file (e.g., '15'). Use with entity_type='file_blocks'.",
                                },
                                "tag_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the tag (e.g., '1', '30'). Use with entity_type='tags'.",
                                },
                                "document_id": {
                                    "type": "string",
                                    "description": "The ID of the document the tag is attached to (e.g., '5'). Use with entity_type='tags'.",
                                },
                                "tag_name": {
                                    "type": "string",
                                    "description": "The exact name of the tag to filter by (e.g., 'important', 'draft'). Use with entity_type='tags'.",
                                },
                                "added_by": {
                                    "type": "string",
                                    "description": "The user_id who added the tag (e.g., '7'). Use with entity_type='tags'.",
                                },
                            },
                        },
                    },
                    "required": ["entity_type"],
                },
            },
        }