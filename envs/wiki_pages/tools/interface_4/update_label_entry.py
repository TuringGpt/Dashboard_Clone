import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class UpdateLabelEntry(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        fields: Dict[str, Any]
    ) -> str:
        """
        Update a label on a doc (ClickUp logic).
        Wraps arguments in a 'fields' dictionary as per documentation.
        """
        # Unwrap fields
        doc_id = fields.get("doc_id")
        old_label_name = fields.get("old_label_name")
        new_label_name = fields.get("new_label_name")
        updated_by = fields.get("updated_by")
        
        page_labels = data.get("page_labels", {})
        pages = data.get("pages", {})
        users = data.get("users", {})
        
        # Validate required parameters
        if not all([doc_id, old_label_name, new_label_name, updated_by]):
            return json.dumps({
                "success": False,
                "error": "Missing required fields in 'fields' dict: doc_id, old_label_name, new_label_name, and updated_by are required"
            })
        
        # Validate doc exists
        if doc_id not in pages:
            return json.dumps({
                "success": False,
                "error": f"Doc with ID '{doc_id}' not found"
            })
        
        # Validate user exists
        if updated_by not in users:
            return json.dumps({
                "success": False,
                "error": f"User with ID '{updated_by}' not found"
            })
        
        user = users[updated_by]
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID '{updated_by}' is not active"
            })
        
        # Find the label to update
        label_to_update = None
        label_id_to_update = None
        for label_id, label in page_labels.items():
            if label.get("page_id") == doc_id and label.get("label_name") == old_label_name:
                label_to_update = label
                label_id_to_update = label_id
                break
        
        if not label_to_update:
            return json.dumps({
                "success": False,
                "error": f"Label '{old_label_name}' not found on doc '{doc_id}'"
            })
        
        # Check if new label name already exists on this doc (and it's not the same label)
        for label_id, label in page_labels.items():
            if label_id != label_id_to_update and label.get("page_id") == doc_id and label.get("label_name") == new_label_name:
                return json.dumps({
                    "success": False,
                    "error": f"Label '{new_label_name}' already exists on doc '{doc_id}'"
                })
        
        # Update the label
        page_labels[label_id_to_update]["label_name"] = new_label_name
        
        # Map database fields to interface fields
        updated_label = page_labels[label_id_to_update]
        response_label = {
            "label_id": updated_label.get("page_label_id"),
            "doc_id": updated_label.get("page_id"),
            "label_name": updated_label.get("label_name"),
            "added_by": updated_label.get("added_by"),
            "added_at": updated_label.get("added_at")
        }
        
        return json.dumps({
            "success": True,
            "label": response_label
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "update_label_entry", 
                "description": "Update an existing label's name on a doc. Requires a 'fields' object containing doc_id, old_label_name, new_label_name, and updated_by",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fields": {
                            "type": "object",
                            "properties": {
                                "doc_id": {
                                    "type": "string",
                                    "description": "ID of the doc containing the label"
                                },
                                "old_label_name": {
                                    "type": "string",
                                    "description": "Current name of the label to update"
                                },
                                "new_label_name": {
                                    "type": "string",
                                    "description": "New name for the label"
                                },
                                "updated_by": {
                                    "type": "string",
                                    "description": "User ID of the person updating the label"
                                }
                            },
                            "required": ["doc_id", "old_label_name", "new_label_name", "updated_by"]
                        }
                    },
                    "required": ["fields"]
                }
            }
        }

