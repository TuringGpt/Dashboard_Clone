import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class LocatePage(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        page_id: Optional[str] = None,
        title: Optional[str] = None,
        doc_id: Optional[str] = None,
        parent_page_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Retrieve page information.
        Maps Coda pages to Confluence pages.
        """

        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})
        pages = data.get("pages", {})
        if not isinstance(pages, dict):
            return json.dumps({"success": False, "error": "Corrupted pages store"})
        
        page_labels = data.get("page_labels", {})
        smart_links = data.get("smart_links", {})
        
        # Build indexes for labels and pack_cards by page_id for O(1) lookup
        labels_by_page = {}
        for label_id, label in page_labels.items():
            pid = label.get("page_id")
            if pid not in labels_by_page:
                labels_by_page[pid] = []
            labels_by_page[pid].append(label)
        
        pack_cards_by_page = {}
        for link_id, link in smart_links.items():
            pid = link.get("host_page_id")
            if pid not in pack_cards_by_page:
                pack_cards_by_page[pid] = []
            pack_cards_by_page[pid].append(link)

        def format_page(pid: str, record: Dict[str, Any]) -> Dict[str, Any]:
            payload = dict(record)
            payload["page_id"] = pid
            if "space_id" in payload:
                payload["doc_id"] = payload.pop("space_id")
            
            # Add labels and pack_cards using the pre-built indexes
            payload["labels"] = labels_by_page.get(pid, [])
            payload["pack_cards"] = pack_cards_by_page.get(pid, [])
            
            return payload

        # if page_id:
        #     page = pages.get(page_id)
        #     if not page:
        #         return json.dumps({"success": False, "error": f"Page '{page_id}' not found"})
        #     return json.dumps({"success": True, "page": format_page(page_id, page)})

        filters = {}
        if title:
            filters["title"] = title
        if doc_id:
            filters["space_id"] = doc_id
        if parent_page_id:
            filters["parent_page_id"] = parent_page_id
        if status:
            filters["status"] = status
        if page_id:
            filters["page_id"] = page_id

        if not filters:
            return json.dumps({"success": False, "page": None, "pages": []})

        matches = []
        for pid, record in pages.items():
            if all(record.get(k) == v for k, v in filters.items()):
                matches.append(format_page(pid, record))

        if not matches:
            return json.dumps({"success": False, "error": "No pages found matching the criteria"})
        return json.dumps({"success": True, "pages": matches, "count": len(matches)})

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "locate_page",
                "description": "Retrieve page information. Can search by page_id, title, doc_id, parent_page_id, or status (current, draft, locked, archived, deleted). Returns page details including content, parent relationships, and metadata.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "Unique page identifier."},
                        "title": {"type": "string", "description": "Page title for exact matching."},
                        "doc_id": {"type": "string", "description": "Doc identifier that owns the page."},
                        "parent_page_id": {"type": "string", "description": "Parent page identifier (for sub-pages)."},
                        "status": {
                            "type": "string",
                            "description": "Page status (current, draft, locked, archived, deleted).",
                        },
                    },
                    "required": [],
                },
            },
        }
