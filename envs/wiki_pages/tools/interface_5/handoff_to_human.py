from typing import Any, Dict
from tau_bench.envs.tool import Tool

class HandoffToHuman(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], summary: str) -> str:
        return "Transfer successful"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "handoff_to_human",
                "description": "Transfer the user to a human agent with a summary of the issue. Use only when explicitly requested or when automated tools cannot resolve the request.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "A concise summary of why the handoff is required.",
                        },
                    },
                    "required": ["summary"],
                },
            },
        }
