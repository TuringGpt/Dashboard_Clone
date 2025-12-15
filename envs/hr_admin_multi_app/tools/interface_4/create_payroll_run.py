import json
from datetime import datetime
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class CreatePayrollRun(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        start_date: str,
        end_date: str,
        frequency: str,
        status: str = 'open'
    ) -> str:
        """
        Create a new payroll cycle/run.
        """
        payroll_cycles = data.get("payroll_cycles", {})
        timestamp = "2025-11-16T23:59:00"
        
        # --- 1. Basic Field Validation ---
        if not start_date:
            return json.dumps({"success": False, "error": "start_date is required"})
        
        if not end_date:
            return json.dumps({"success": False, "error": "end_date is required"})
        
        if not frequency:
            return json.dumps({"success": False, "error": "frequency is required"})
        
        # Validate status
        valid_statuses = ["open", "closed"]
        if status not in valid_statuses:
            return json.dumps({
                "success": False,
                "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            })

        # --- 2. Date Logic Validation ---
        try:
            # Parse dates to datetime objects for comparison
            new_start = datetime.strptime(start_date, "%Y-%m-%d")
            new_end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return json.dumps({
                "success": False, 
                "error": "Invalid date format. Dates must be in YYYY-MM-DD format."
            })

        # Check: start_date cannot be after end_date
        if new_start > new_end:
            return json.dumps({
                "success": False,
                "error": f"start_date ({start_date}) cannot be after end_date ({end_date})"
            })

        # --- 3. Overlap Validation ---
        # Check against every existing cycle for time overlaps
        for cycle_id, cycle in payroll_cycles.items():
            existing_start_str = cycle.get("start_date")
            existing_end_str = cycle.get("end_date")
            
            # Skip records with missing dates to avoid crash, though they shouldn't exist
            if not existing_start_str or not existing_end_str:
                continue

            try:
                existing_start = datetime.strptime(existing_start_str, "%Y-%m-%d")
                existing_end = datetime.strptime(existing_end_str, "%Y-%m-%d")
            except ValueError:
                continue # Skip malformed existing records

            # Overlap Formula: (StartA <= EndB) and (EndA >= StartB)
            # If this condition is true, the two ranges overlap
            if new_start <= existing_end and new_end >= existing_start:
                return json.dumps({
                    "success": False,
                    "error": (
                        f"The new date range ({start_date} to {end_date}) overlaps with "
                        f"existing cycle {cycle_id} ({existing_start_str} to {existing_end_str})"
                    )
                })

        # --- 4. Creation Logic ---
        def generate_id(table: Dict[str, Any]) -> str:
            if not table:
                return "1"
            return str(max(int(k) for k in table.keys()) + 1)
        
        new_cycle_id = generate_id(payroll_cycles)
        
        new_cycle = {
            "cycle_id": new_cycle_id,
            "start_date": start_date,
            "end_date": end_date,
            "frequency": frequency,
            "status": status,
            "created_at": timestamp,
            "last_updated": timestamp
        }
        
        payroll_cycles[new_cycle_id] = new_cycle
        
        return json.dumps({
            "success": True,
            "payroll_cycle": new_cycle
        })
    
    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_payroll_run",
                "description": "Create a new payroll cycle. Validates that start_date is before end_date and ensures no overlap with existing cycles.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format (required)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (required)"
                        },
                        "frequency": {
                            "type": "string",
                            "description": "Payroll frequency (required)"
                        },
                        "status": {
                            "type": "string",
                            "description": "Cycle status: open, closed (optional, default: 'open')",
                            "enum": ["open", "closed"]
                        }
                    },
                    "required": ["start_date", "end_date", "frequency"]
                }
            }
        }