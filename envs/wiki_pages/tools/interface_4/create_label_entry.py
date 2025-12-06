import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class CreateLabelEntry(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        doc_id: str,
        label_name: str,
        added_by: str
    ) -> str:
        """
        Add a label to a doc (ClickUp logic).
        """
        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)
        
        timestamp = "2025-12-02T12:00:00"
        page_labels = data.get("page_labels", {})
        pages = data.get("pages", {})
        users = data.get("users", {})
        
        # Validate required parameters
        if not all([doc_id, label_name, added_by]):
            return json.dumps({
                "success": False,
                "error": "Missing required parameters: doc_id, label_name, and added_by are required"
            })
        
        # Validate doc exists
        if doc_id not in pages:
            return json.dumps({
                "success": False,
                "error": f"Doc with ID '{doc_id}' not found"
            })
        
        # Validate user exists
        if added_by not in users:
            return json.dumps({
                "success": False,
                "error": f"User with ID '{added_by}' not found"
            })
        
        user = users[added_by]
        if user.get("status") != "active":
            return json.dumps({
                "success": False,
                "error": f"User with ID '{added_by}' is not active"
            })
        
        # Check if label already exists on this doc
        for label_id, label in page_labels.items():
            if label.get("page_id") == doc_id and label.get("label_name") == label_name:
                return json.dumps({
                    "success": False,
                    "error": f"Label '{label_name}' already exists on doc '{doc_id}'"
                })
        
        # Generate new label ID
        new_label_id = generate_id(page_labels)
        
        # Create new label for database (using database field names)
        db_label = {
            "page_label_id": new_label_id,
            "page_id": doc_id,
            "label_name": label_name,
            "added_by": added_by,
            "added_at": timestamp
        }
        
        page_labels[new_label_id] = db_label
        
        # Create response object with interface field names
        response_label = {
            "label_id": new_label_id,
            "doc_id": doc_id,
            "label_name": label_name,
            "added_by": added_by,
            "added_at": timestamp
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
                "name": "create_label_entry", 
                "description": "Add a new label to a doc with specified label name and user attribution",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "ID of the doc to add the label to"
                        },
                        "label_name": {
                            "type": "string",
                            "description": "Name of the label to add"
                        },
                        "added_by": {
                            "type": "string",
                            "description": "User ID of the person adding the label"
                        }
                    },
                    "required": ["doc_id", "label_name", "added_by"]
                }
            }
        }

