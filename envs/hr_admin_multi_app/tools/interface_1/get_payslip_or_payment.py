import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool


class GetPayslipOrPayment(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        entity_type: str,
        entity_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        cycle_id: Optional[str] = None,
        status: Optional[str] = None,
        payment_method: Optional[str] = None,
        source_payslip_id: Optional[str] = None,
    ) -> str:
        """
        Fetches payslip or payment details based on the entity type and provided filters.
        """
        
        if not isinstance(data, dict):
            return json.dumps({"error": "Invalid data format"})

        # Validate required field
        if not entity_type:
            return json.dumps({
                "error": "Missing required parameter: entity_type"
            })

        # Validate entity_type
        valid_entity_types = ["payslip", "payment"]
        if entity_type not in valid_entity_types:
            return json.dumps({
                "error": f"Invalid entity_type. Must be one of: {', '.join(valid_entity_types)}"
            })

        if entity_type == "payslip":
            payslips = data.get("payslips", {})
            
            # If specific entity_id is provided, return only that payslip
            if entity_id:
                entity_id = str(entity_id)
                if entity_id not in payslips:
                    return json.dumps({
                        "error": f"Payslip with ID '{entity_id}' not found"
                    })
                
                return json.dumps({
                    "success": True,
                    "entity_type": "payslip",
                    "count": 1,
                    "results": [payslips[entity_id]]
                })
            
            # Filter payslips based on provided criteria
            results = []
            for payslip in payslips.values():
                match = True
                
                if employee_id:
                    if payslip.get("employee_id") != str(employee_id):
                        match = False
                
                if cycle_id and match:
                    if payslip.get("cycle_id") != str(cycle_id):
                        match = False
                
                if status and match:
                    if payslip.get("status") != status:
                        match = False
                
                if match:
                    results.append(payslip)
            
            return json.dumps({
                "success": True,
                "entity_type": "payslip",
                "count": len(results),
                "results": results
            })
        
        elif entity_type == "payment":
            payments = data.get("payments", {})
            payslips = data.get("payslips", {})
            
            # If specific entity_id is provided, return only that payment
            if entity_id:
                entity_id = str(entity_id)
                if entity_id not in payments:
                    return json.dumps({
                        "error": f"Payment with ID '{entity_id}' not found"
                    })
                
                return json.dumps({
                    "success": True,
                    "entity_type": "payment",
                    "count": 1,
                    "results": [payments[entity_id]]
                })
            
            # Filter payments based on provided criteria
            results = []
            for payment in payments.values():
                match = True
                
                # Check employee_id match
                if employee_id:
                    if payment.get("employee_id") != str(employee_id):
                        match = False
                
                # Check source_payslip_id match
                if source_payslip_id and match:
                    if payment.get("source_payslip_id") != str(source_payslip_id):
                        match = False
                
                # Check status match
                if status and match:
                    if payment.get("status") != status:
                        match = False
                
                # Check payment_method match
                if payment_method and match:
                    if payment.get("payment_method") != payment_method:
                        match = False
                
                if match:
                    results.append(payment)
            
            return json.dumps({
                "success": True,
                "entity_type": "payment",
                "count": len(results),
                "results": results
            })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_payslip_or_payment",
                "description": "Fetches payslip or payment details from the HR payroll system with comprehensive filtering options.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Type of entity to fetch: 'payslip' or 'payment' (required)"
                        },
                        "entity_id": {
                            "type": "string",
                            "description": "ID of the specific payslip or payment to retrieve (optional). When provided, returns only that entity."
                        },
                        "employee_id": {
                            "type": "string",
                            "description": "Filter by employee ID (optional)"
                        },
                        "cycle_id": {
                            "type": "string",
                            "description": (
                                "Filter by payroll cycle ID (optional). "
                                "Only applicable for entity_type='payslip'. Filters payslips directly by cycle_id."
                            )
                        },
                        "status": {
                            "type": "string",
                            "description": (
                                "Filter by status (optional). "
                                "For payslips: 'draft', 'released', 'updated'. "
                                "For payments: 'pending', 'completed', 'failed'."
                            )
                        },
                        "payment_method": {
                            "type": "string",
                            "description": "Filter by payment method (optional). For payments: 'Bank Transfer' or 'Check'. Only applicable for entity_type='payment'."
                        },
                        "source_payslip_id": {
                            "type": "string",
                            "description": "Filter by source payslip ID (optional). Only applicable for entity_type='payment'."
                        }
                    },
                    "required": ["entity_type"]
                }
            }
        }