import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool


class GetActiveDepartment(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        department_id: str = None,
        department_name: str = None,
    ) -> Dict[str, Any]:
        """
        Retrieve active department details from the HR database.
        Returns department information if the department exists and has status "active".
        Can filter by department_id or department_name.
        """
        if not isinstance(data, dict):
            return {
                "success": False,
                "error": "Invalid data format"
            }

        departments = data.get("departments", {})
        
        if not department_id and not department_name:
            return {
                "success": False,
                "error": "Either department_id or department_name is required"
            }

        department = None
        
        # Search by department_id if provided
        if department_id:
            department = departments.get(department_id)
            if not department:
                return {
                    "success": False,
                    "error": f"Department with id '{department_id}' not found"
                }
        # Search by department_name if provided
        elif department_name:
            for dept_id, dept_data in departments.items():
                if dept_data.get("name") == department_name:
                    department = dept_data
                    break
            if not department:
                return {
                    "success": False,
                    "error": f"Department with name '{department_name}' not found"
                }

        status = department.get("status")
        
        if status != "active":
            return {
                "success": False,
                "error": f"Department with id '{department_id}' is not active. Current status: '{status}'"
            }

        return {
            "success": True,
            "department": {
                "department_id": department.get("department_id"),
                "name": department.get("name"),
                "status": department.get("status"),
                "head_of_department_id": department.get("head_of_department_id"),
                "created_at": department.get("created_at"),
                "last_updated": department.get("last_updated")
            }
        }

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_active_department",
                "description": "Retrieve active department details. Returns department information if the department exists and has status 'active'. Returns an error if the department is not found or is not active. Can filter by department_id or department_name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "department_id": {
                            "type": "string",
                            "description": "Unique department identifier. Either department_id or department_name must be provided.",
                        },
                        "department_name": {
                            "type": "string",
                            "description": "Department name. Either department_id or department_name must be provided.",
                        },
                    },
                    "required": [],
                },
            },
        }

