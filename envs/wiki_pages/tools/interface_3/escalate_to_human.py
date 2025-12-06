import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool


class EscalateToHuman(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        reason: str,
        context: Optional[str] = None,
    ) -> str:
        """
        Escalate the conversation to a human agent.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not reason:
            return json.dumps({"error": "Missing required parameter: reason is required"})

        transfer_record = {
            "status": "escalated",
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
                "name": "escalate_to_human",
                "description": (
                    "Escalates the current conversation or task to a human agent. "
                    "Use this tool when the request cannot be handled automatically, "
                    "requires human judgment, or when explicitly requested by the user."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": (
                                "The reason for escalating to a human agent (required). "
                                "Provide a clear explanation of why human intervention is needed."
                            ),
                        },
                        "context": {
                            "type": "string",
                            "description": (
                                "Additional context or information to pass to the human agent (optional). "
                                "Include any relevant details that would help the human agent assist the user."
                            ),
                        },
                    },
                    "required": ["reason"],
                },
            },
        }

