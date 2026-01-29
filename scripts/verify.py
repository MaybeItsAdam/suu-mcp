from src.server import _learn_form_structure, FORMS_DIR
import os

def test_learning():
    url = "https://studentsunionucl.org/forms/payment-request-form?webform_access_group=82235"
    form_id = "payment_request"
    
    print(f"Testing learning for {form_id} at {url}")
    result = _learn_form_structure(url, form_id)
    print("Result:", result)
    
    config_path = os.path.join(FORMS_DIR, f"{form_id}.json")
    if os.path.exists(config_path):
        print(f"SUCCESS: Config file generated at {config_path}")
        with open(config_path, "r") as f:
            print("Config content snippet:", f.read()[:500])
    else:
        print("FAILURE: Config file not found.")

if __name__ == "__main__":
    test_learning()
