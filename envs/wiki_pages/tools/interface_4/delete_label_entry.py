import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteLabelEntry(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        label_id: str,
        label_name: str
    ) -> str:
        """
        Delete a label from a doc (ClickUp logic).
        """
        page_labels = data.get("page_labels", {})
        
        # Validate required parameters
        if not all([label_id, label_name]):
            return json.dumps({
                "success": False,
                "error": "Missing required parameters: label_id and label_name are required"
            })
        
        # Validate label exists
        if label_id not in page_labels:
            return json.dumps({
                "success": False,
                "error": f"Label with ID '{label_id}' not found"
            })
        
        # Verify label name matches
        label = page_labels[label_id]
        if label.get("label_name") != label_name:
            return json.dumps({
                "success": False,
                "error": f"Label name mismatch. Expected '{label_name}', found '{label.get('label_name')}'"
            })
        
        # Delete the label
        deleted_label = page_labels.pop(label_id)
        
        # Map database fields to interface fields
        response_label = {
            "label_id": deleted_label.get("page_label_id"),
            "doc_id": deleted_label.get("page_id"),
            "label_name": deleted_label.get("label_name"),
            "added_by": deleted_label.get("added_by"),
            "added_at": deleted_label.get("added_at")
        }
        
        return json.dumps({
            "success": True,
            "message": f"Label '{label_name}' with ID '{label_id}' has been deleted",
            "deleted_label": response_label
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_label_entry", 
                "description": "Permanently delete a label entry from a doc by label_id",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "label_id": {
                            "type": "string",
                            "description": "ID of the label to delete"
                        },
                        "label_name": {
                            "type": "string",
                            "description": "Name of the label to delete (for verification)"
                        }
                    },
                    "required": ["label_id", "label_name"]
                }
            }
        }

