import json
from typing import Any, Dict

from tau_bench.envs.tool import Tool


class CompleteEmployeeOffboarding(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        employee_id: str,
        force_complete: bool = False,
    ) -> str:
        """
        Complete the offboarding process for an employee.
        
        Args:
            data: The database dictionary containing all tables.
            employee_id: The ID of the employee being offboarded (required).
            force_complete: Force completion even if tasks are pending (True/False). 
                Defaults to False.
        
        Returns:
            JSON string with the completed exit case and updated employee records.
        """
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        if not employee_id:
            return json.dumps({"error": "Missing required parameter: employee_id is required"})

        employee_id = str(employee_id)
        exit_cases = data.get("exit_cases", {})
        checklists = data.get("checklists", {})
        checklist_tasks = data.get("checklist_tasks", {})
        employees = data.get("employees", {})
        employee_assets = data.get("employee_assets", {})
        finance_settlements = data.get("finance_settlements", {})
        contracts = data.get("contracts", {})
        payslips = data.get("payslips", {})
        payments = data.get("payments", {})

        # Validate employee exists
        if employee_id not in employees:
            return json.dumps({"error": f"Employee with ID '{employee_id}' not found"})

        # Find the exit case for this employee
        exit_case = None
        exit_case_id = None
        for case_id, case in exit_cases.items():
            if case.get("employee_id") == employee_id:
                exit_case = case
                exit_case_id = case_id
                break

        if not exit_case:
            return json.dumps({
                "error": f"No exit case found for employee '{employee_id}'. Use initiate_offboarding first."
            })
        
        if exit_case.get("exit_clearance_status") == "cleared":
            return json.dumps({"error": f"Exit case for employee '{employee_id}' is already completed"})

        timestamp = "2025-11-16T23:59:00"

        # Find the offboarding checklist for this employee
        offboarding_checklist_id = None
        for checklist_id, checklist in checklists.items():
            if (checklist.get("employee_id") == employee_id and 
                checklist.get("checklist_type") == "offboarding"):
                offboarding_checklist_id = checklist_id
                break

        # Check for pending tasks in the offboarding checklist
        pending_tasks = []
        if offboarding_checklist_id:
            for task_id, task in checklist_tasks.items():
                if (task.get("checklist_id") == offboarding_checklist_id and 
                    task.get("status") != "completed"):
                    pending_tasks.append({
                        "task_id": task_id,
                        "task_name": task.get("name"),
                        "status": task.get("status"),
                    })

        # Auto-complete all pending tasks
        if offboarding_checklist_id:
            for task_id, task in checklist_tasks.items():
                if task.get("checklist_id") == offboarding_checklist_id:
                    task["status"] = "completed"
                    task["last_updated"] = timestamp

        # Update all assets to returned status
        for asset_id, asset in employee_assets.items():
            if asset.get("employee_id") == employee_id:
                asset["status"] = "returned"
                asset["last_updated"] = timestamp

        # Check payment and payslip status
        payment_status_issues = []
        payslip_status_issues = []
        
        for payslip_id, payslip in payslips.items():
            if payslip.get("employee_id") == employee_id:
                if payslip.get("status") not in ["released", "updated"]:
                    payslip_status_issues.append({
                        "payslip_id": payslip_id,
                        "status": payslip.get("status"),
                    })

        for payment_id, payment in payments.items():
            if payment.get("employee_id") == employee_id:
                if payment.get("status") != "completed":
                    payment_status_issues.append({
                        "payment_id": payment_id,
                        "status": payment.get("status"),
                    })

        if (payslip_status_issues or payment_status_issues) and not force_complete:
            return json.dumps({
                "error": "Cannot complete offboarding. Payslip or payment not finalized. Use force_complete=True to override.",
                "payslip_issues": payslip_status_issues,
                "payment_issues": payment_status_issues,
            })

        # Update finance settlement to cleared
        for settlement_id, settlement in finance_settlements.items():
            if settlement.get("employee_id") == employee_id:
                settlement["is_cleared"] = True
                settlement["last_updated"] = timestamp

        # Update exit case
        exit_case["exit_clearance_status"] = "cleared"
        exit_case["last_updated"] = timestamp

        # Update offboarding checklist status to completed
        if offboarding_checklist_id and offboarding_checklist_id in checklists:
            checklists[offboarding_checklist_id]["status"] = "completed"
            checklists[offboarding_checklist_id]["last_updated"] = timestamp

        # Update finance settlement to cleared
        for settlement_id, settlement in finance_settlements.items():
            if settlement.get("employee_id") == employee_id:
                settlement["is_cleared"] = True
                settlement["last_updated"] = timestamp

        # Update payslips to released
        for payslip_id, payslip in payslips.items():
            if payslip.get("employee_id") == employee_id and payslip.get("status") == "draft":
                payslip["status"] = "released"
                payslip["last_updated"] = timestamp

        # Update payments to completed
        for payment_id, payment in payments.items():
            if payment.get("employee_id") == employee_id and payment.get("status") == "pending":
                payment["status"] = "completed"
                payment["payment_date"] = timestamp
                payment["last_updated"] = timestamp

        # Update employee status
        if employee_id in employees:
            employee = employees[employee_id]
            employee["status"] = "inactive"
            employee["flag_pending_settlement"] = False
            employee["last_updated"] = timestamp

        # Terminate contract if exists
        for contract_id, contract in contracts.items():
            if contract.get("employee_id") == employee_id and not contract.get("is_terminated"):
                contract["is_terminated"] = True
                contract["termination_date"] = exit_case.get("exit_date")
                contract["last_updated"] = timestamp

        return json.dumps({
            "exit_case_id": exit_case_id,
            "employee_id": employee_id,
            "exit_case": exit_case,
            "employee_status": employees.get(employee_id, {}).get("status"),
            "checklist_id": offboarding_checklist_id,
            "completion_message": f"Offboarding completed for employee {employee_id}",
            "status_updates": {
                "exit_case_status": "cleared",
                "checklist_status": "completed",
                "settlement_status": "cleared",
                "payslips_status": "released",
                "payments_status": "completed",
                "employee_status": "inactive",
                "contract_terminated": True,
            }
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "complete_employee_offboarding",
                "description": (
                    "Completes the offboarding process for an employee by updating all related entities. "
                    "Updates exit case status to 'cleared', offboarding checklist and all its tasks to 'completed', "
                    "finance settlement to 'cleared', payslips to 'released', payments to 'completed', "
                    "employee status to 'inactive', and terminates the employee contract. "
                    "Validates that payslips are finalized (released/updated) and payments are completed before completion. "
                    "Automatically finds the employee's exit case and offboarding checklist. "
                    "Requires that initiate_offboarding has already been called for the employee."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "The ID of the employee being offboarded (required).",
                        },
                        "force_complete": {
                            "type": "boolean",
                            "description": (
                                "Force completion even if tasks, assets, settlements, "
                                "payslips, or payments are not finalized (True/False). Defaults to False."
                            ),
                        },
                    },
                    "required": ["employee_id"],
                },
            },
        }