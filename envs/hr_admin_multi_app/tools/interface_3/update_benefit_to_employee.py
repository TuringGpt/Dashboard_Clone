import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class UpdateBenefitToEmployee(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        employee_id: str,
        plan_id: str,
        start_date: str,
        cancel: bool = False,
    ) -> str:
        """
        Update, assign, or cancel a benefit plan enrollment for an employee.
        
        Args:
            data: The database dictionary containing all tables.
            employee_id: The ID of the employee (required).
            plan_id: The ID of the benefit plan (required).
            start_date: The enrollment start date in format (YYYY-MM-DD) (required).
            cancel: If True, cancels/deactivates the enrollment (optional, default False).
        
        Returns:
            JSON string with the updated or created benefit enrollment record.
        """
        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            max_id = 0
            for k in table.keys():
                try:
                    max_id = max(max_id, int(k))
                except ValueError:
                    continue
            return str(max_id + 1)

        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        # Validate required parameters
        if not employee_id:
            return json.dumps({"error": "Missing required parameter: employee_id is required"})
        if not plan_id:
            return json.dumps({"error": "Missing required parameter: plan_id is required"})
        if not start_date:
            return json.dumps({"error": "Missing required parameter: start_date is required"})

        employee_id = str(employee_id)
        plan_id = str(plan_id)

        employees = data.get("employees", {})
        benefit_plans = data.get("benefit_plans", {})
        benefit_enrollments = data.get("benefit_enrollments", {})

        # Verify target employee exists and is active
        if employee_id not in employees:
            return json.dumps({"error": f"Employee with ID '{employee_id}' not found"})
        
        target_employee = employees[employee_id]
        if target_employee.get("status") != "active":
            return json.dumps({"error": f"Employee '{employee_id}' is not active"})

        # Verify benefit plan exists and is active
        if plan_id not in benefit_plans:
            return json.dumps({"error": f"Benefit plan with ID '{plan_id}' not found"})

        plan = benefit_plans[plan_id]
        if not cancel and plan.get("status") == "inactive":
            return json.dumps({"error": f"Cannot enroll in inactive benefit plan '{plan_id}'"})

        timestamp = "2025-11-16T23:59:00"

        # Check for existing enrollment and update it
        for enrollment_id, enrollment in benefit_enrollments.items():
            if enrollment.get("employee_id") == employee_id and enrollment.get("plan_id") == plan_id:
                enrollment["start_date"] = start_date
                enrollment["is_active"] = not cancel  # Deactivate if cancel=True
                enrollment["last_updated"] = timestamp
                if cancel:
                    enrollment["end_date"] = start_date
                return json.dumps(enrollment)

        # Create new enrollment if none exists (only if not canceling)
        if cancel:
            return json.dumps({
                "error": f"No existing enrollment found for employee '{employee_id}' and plan '{plan_id}' to cancel"
            })
        
        enrollment_id = generate_id(benefit_enrollments)
        new_enrollment = {
            "enrollment_id": enrollment_id,
            "employee_id": employee_id,
            "plan_id": plan_id,
            "start_date": start_date,
            "is_active": True,
            "created_at": timestamp,
            "last_updated": timestamp,
        }

        benefit_enrollments[enrollment_id] = new_enrollment
        data["benefit_enrollments"] = benefit_enrollments

        return json.dumps(new_enrollment)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "update_benefit_to_employee",
                "description": (
                    "Updates, assigns, or cancels a benefit plan enrollment for an employee. "
                    "Verifies the target employee is active. "
                    "If an enrollment exists, it updates the start date or cancels it (if cancel=true). "
                    "If no enrollment exists and cancel=false, it creates a new one. "
                    "Set cancel=true to deactivate/remove a benefit plan assignment."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "The ID of the employee whose enrollment is being updated (required).",
                        },
                        "plan_id": {
                            "type": "string",
                            "description": "The ID of the benefit plan (required).",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "The enrollment start date (or end date if canceling) in format (YYYY-MM-DD) (required).",
                        },
                        "cancel": {
                            "type": "boolean",
                            "description": "Set to true to cancel/deactivate the enrollment. Defaults to false (optional).",
                        },
                    },
                    "required": ["employee_id", "plan_id", "start_date"],
                },
            },
        }
