import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool

class GetList(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        list_id: Optional[str] = None,
        title: Optional[str] = None,
        site_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> str:
        """
        Get database(s) by various criteria.
        """
        databases = data.get("databases", {})
        spaces = data.get("spaces", {})

        # Validate status
        if status and status not in ["current", "archived", "deleted"]:
            return json.dumps({
                "error": "status must be one of: 'current', 'archived', 'deleted'"
            })

        # Validate site_id
        if site_id and site_id not in spaces:
            return json.dumps({
                "error": f"Site with ID {site_id} not found"
            })

        # If fetching by list_id
        if list_id:
            if list_id not in databases:
                return json.dumps({
                    "error": f"List with ID {list_id} not found"
                })

            database = databases[list_id]

            # Apply filters
            if title and database.get("title") != title:
                return json.dumps({
                    "error": f"List with ID {list_id} does not match title filter"
                })

            if site_id and database.get("host_space_id") != site_id:
                return json.dumps({
                    "error": f"List with ID {list_id} does not match site_id filter"
                })

            if status and database.get("status") != status:
                return json.dumps({
                    "error": f"List with ID {list_id} does not match status filter"
                })

            # Return with renamed fields
            db_copy = dict(database)
            db_copy["list_id"] = list_id
            db_copy.pop("database_id", None)
            db_copy.pop("host_page_id", None)
            # host_space_id → host_site_id (API only)
            if "host_space_id" in db_copy:
                db_copy["host_site_id"] = db_copy.pop("host_space_id")

            return json.dumps({
                "list": db_copy,
                "count": 1
            })

        # Otherwise filter results
        results = []
        for db_id, database in databases.items():
            match = True

            if title and database.get("title") != title:
                match = False

            if site_id and database.get("host_space_id") != site_id:
                match = False

            if status and database.get("status") != status:
                match = False

            if match:
                db_copy = dict(database)
                db_copy["list_id"] = db_id
                db_copy.pop("database_id", None)

                # host_space_id → host_site_id
                if "host_space_id" in db_copy:
                    db_copy["host_site_id"] = db_copy.pop("host_space_id")
                db_copy.pop("host_page_id", None)
                results.append(db_copy)

        if not results:
            return json.dumps({
                "error": "No list found matching the criteria",
                "count": 0,
                "results": []
            })

        return json.dumps({
            "count": len(results),
            "results": results
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_list",
                "description": "Get list(s) by filters. Output uses list_id and host_site_id.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "list_id": {
                            "type": "string",
                            "description": "ID of specific list"
                        },
                        "title": {
                            "type": "string",
                            "description": "Filter by title"
                        },
                        "site_id": {
                            "type": "string",
                            "description": "Filter by site"
                        },
                        "status": {
                            "type": "string",
                            "description": "Status: 'current', 'archived', 'deleted'"
                        }
                    }
                }
            }
        }
