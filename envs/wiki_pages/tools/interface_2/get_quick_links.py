import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class GetQuickLinks(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        quicklink_id: Optional[str] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
        host_page_id: Optional[str] = None
    ) -> str:
        """
        Get quick links by various criteria.
        """
        quicklinks = data.get("smart_links", {})
        results = []
        for ql_id, ql in quicklinks.items():
            if quicklink_id and ql_id != quicklink_id:
                continue
            if title and ql.get("title") != title:
                continue
            if url and ql.get("url") != url:
                continue
            if host_page_id and ql.get("host_page_id") != host_page_id:
                continue
            target_type = ql.pop("target_type", "unknown")
            target_dict = {
                "database": "list",
                "page": "page",
                "whiteboard": "whiteboard",
                "space": "site",
                "external": "external"
            }
            ql["target_type"] =  target_dict.get(target_type, "unknown")
            ql["quicklink_id"] = ql.pop("smart_link_id", ql_id)
            results.append(ql)
        return json.dumps({
            "success": True,
            "count": len(results),
            "results": results
        }) 

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_quick_links",
                "description": "Get's the list of quick links by various filters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "quicklink_id": {
                            "type": "string",
                            "description": "ID of the quick link."
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the quick link."
                        },
                        "url": {
                            "type": "string",
                            "description": "URL of the quick link."
                        },
                        "host_page_id": {
                            "type": "string",
                            "description": "ID of the host page where the quick link is located."
                        }
                    }
                }
            }
        }