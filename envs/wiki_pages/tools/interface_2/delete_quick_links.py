import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteQuickLinks(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], page_id: str, quick_links_id: str, deleted_by: str) -> str:
        """
        Deletes a quick link from the sample data.
        """
        if not isinstance(data, dict):
            return json.dumps(
                {
                    "success": False,
                    "error": "Invalid data format: 'data' must be a dict",
                }
            )
        if deleted_by and deleted_by not in data.get("users", {}):
            return json.dumps(
                {
                    "success": False,
                    "error": f"User with ID '{deleted_by}' not found",
                }
            )
        if page_id and page_id not in data.get("pages", {}):
            return json.dumps(
                {
                    "success": False,
                    "error": f"Page with ID '{page_id}' not found",
                }
            )

        quick_links_dict: Dict[str, Dict[str, Any]] = data.get("smart_links", {})
        if quick_links_id and quick_links_id in quick_links_dict:
            try:
                # verify associated page matches if provided
                target_link = quick_links_dict[quick_links_id]
                if target_link.get("host_page_id") != page_id:
                    return json.dumps(
                        {
                            "success": False,
                            "error": f"Quick link ID '{quick_links_id}' does not match the provided page ID",
                        }
                    )
                # Delete the quick link
                del quick_links_dict[quick_links_id]

                # Update the original data dictionary
                data["smart_links"] = quick_links_dict



                return json.dumps({"success": True, "message": f"quick link '{quick_links_id}' deleted successfully"})

            except (KeyError, TypeError):
                # This should not be hit if the prior 'in' check worked
                pass
        # Return failure if ID is missing or not found
        return json.dumps({"success": False, "error": f"Quick link with ID '{quick_links_id}' not found"})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_quick_links",
                "description": "Delete a quick link from the Wiki system by its ID and URL if provided.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "quick_links_id": {
                            "type": "string",
                            "description": "The unique identifier of the quick link to be deleted.",
                        },
                        "page_id": {
                            "type": "string",
                            "description": "The unique identifier of the page associated with the quick link.",
                        },
                        "deleted_by": {
                            "type": "string",
                            "description": "The user ID of the person deleting the quick link.",
                    },
                    
                },
                "required": ["quick_links_id", "deleted_by"],
            },
        }
        }