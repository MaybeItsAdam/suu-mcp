from src.server import run_form_automation
import json

def test_execution():
    form_id = "payment_request"
    
    # Sample data mapping to our new schema
    data = {
        "description": "Reimbursement for high vis jackets",
        "payee_name": "Shria Jindal",
        "phone_number": "+447761767941",
        "email": "uclmjin@ucl.ac.uk",
        "account_number": "11545515",
        "sort_code": "400407",
        "payee_details_changed": "No"
    }
    
    print(f"Running automation for {form_id}...")
    result = run_form_automation(form_id, json.dumps(data))
    print("Result:", result)

if __name__ == "__main__":
    test_execution()
