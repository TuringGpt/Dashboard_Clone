import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class GetLabel(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        doc_id: str,
        label_name: Optional[str] = None
    ) -> str:
        """
        Find label(s) based on filter criteria (ClickUp logic).
        """
        page_labels = data.get("page_labels", {})
        results = []
        
        for label_id, label in page_labels.items():
            match = True
            
            if doc_id and label.get("page_id") != doc_id:
                match = False
            if label_name and label.get("label_name") != label_name:
                match = False
            
            if match:
                # Map database fields to interface fields
                label_obj = {
                    "label_id": label.get("page_label_id"),
                    "doc_id": label.get("page_id"),
                    "label_name": label.get("label_name"),
                    "added_by": label.get("added_by"),
                    "added_at": label.get("added_at")
                }
                results.append(label_obj)
        
        return json.dumps({
            "success": True,
            "count": len(results),
            "labels": results
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_label", 
                "description": "Retrieve labels from a doc based on doc_id and optional label_name filter",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "Filter by doc ID"
                        },
                        "label_name": {
                            "type": "string",
                            "description": "Filter by label name (optional)"
                        }
                    },
                    "required": ["doc_id"]
                }
            }
        }

