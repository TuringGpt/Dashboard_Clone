import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class DelegateToHuman(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        reason: str,
        context: Optional[str] = None,
    ) -> str:
        """
        Delegate the conversation to a human agent.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})
        
        if not reason:
            return json.dumps({"error": "Missing required parameter: reason is required"})
        
        transfer_record = {
            "status": "delegated",
            "reason": reason,
            "context": context,
            "timestamp": "2025-12-02T12:00:00",
        }
        
        return json.dumps(transfer_record)
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delegate_to_human",
                "description": "Delegate the conversation to a human agent when the request cannot be handled automatically or requires human judgment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for delegating to a human agent with clear explanation",
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context or information to pass to the human agent (optional)",
                        },
                    },
                    "required": ["reason"],
                },
            },
        }

