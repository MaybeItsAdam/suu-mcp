from fastmcp import FastMCP
import os
import json
from .executor import FormExecutor
from .schema import FormDefinition

mcp = FastMCP(
    "SUU-MCP",
    instructions="""
    You are an assistant that can automate UCL Student Union web forms.
    
    CONTEXT:
    - Location: London, UK (University College London)
    - Currency: GBP (£)
    - Date Format: DD/MM/YYYY
    - Banking: Uses UK Sort Code (6 digits) and Account Number (8 digits)
    
    AVAILABLE ACTIONS:
    1. list_available_forms() - See what forms you can fill
    2. run_form_automation(form_id, data) - Fill a form with user's data
    
    WORKFLOW:
    1. First call list_available_forms() to see what's available
    2. Ask the user for the required data fields
    3. Call run_form_automation() with the form_id and data as JSON
    
    IMPORTANT BEHAVIORS:
    - Always confirm with the user before running automation
    - Forms are NEVER submitted - only filled for the user to review
    - A browser window will open so the user can see what's happening
    - The browser stays open after filling so the user can review and submit manually
    
    AUTHENTICATION:
    - Forms require the user to be logged into the UCL system
    - Authentication sessions are saved in files (forms/default_auth.json)
    - Sessions expire after some time (usually hours to days)
    
    IF AUTHENTICATION FAILS (you see "Authentication not configured" or the form redirects to login):
    - Tell the user: "Your session has expired or is not set up."
    - Ask them to run: python save_auth.py
    - This opens a browser where they log in manually, then saves the session
    - After they confirm it's done, you can retry the form automation
    """
)

FORMS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "forms"))
os.makedirs(FORMS_DIR, exist_ok=True)


@mcp.tool()
def list_available_forms() -> str:
    """
    Lists all form automations that are ready to use.
    Call this FIRST to see what forms you can help fill.
    Returns form IDs, descriptions, and the data fields required.
    """
    forms = []
    for filename in os.listdir(FORMS_DIR):
        if filename.endswith(".json") and not filename.endswith("_auth.json"):
            try:
                with open(os.path.join(FORMS_DIR, filename), "r") as f:
                    form_def = json.load(f)
                    form_id = form_def.get("form_id", filename.replace(".json", ""))
                    description = form_def.get("description", "No description")
                    
                    # Build detailed field info
                    fields = form_def.get("fields", [])
                    field_info = []
                    for f in fields:
                        name = f.get("name")
                        desc = f.get("description", "")
                        required = f.get("required", True)
                        options = f.get("options")
                        
                        info = {
                            "name": name,
                            "description": desc,
                            "required": required,
                        }
                        if options:
                            info["allowed_values"] = options
                        field_info.append(info)
                    
                    forms.append({
                        "form_id": form_id,
                        "description": description,
                        "fields": field_info
                    })
            except Exception:
                continue
    
    if not forms:
        return "No forms configured. The user needs to set up form definitions first."
    
    result = "AVAILABLE FORMS:\n\n"
    for form in forms:
        result += f"## {form['form_id']}\n"
        result += f"{form['description']}\n\n"
        result += "Required data fields:\n"
        for field in form['fields']:
            req = "(required)" if field['required'] else "(optional)"
            result += f"  - {field['name']} {req}: {field['description']}\n"
            if 'allowed_values' in field:
                result += f"    Allowed values: {field['allowed_values']}\n"
        result += "\n"
    
    return result


@mcp.tool()
async def run_form_automation(form_id: str, data: str) -> str:
    """
    Fills a web form with the provided data. Opens a visible browser window.
    The form is NEVER submitted - it only fills fields for the user to review.
    
    Args:
        form_id: Which form to fill (get this from list_available_forms)
        data: JSON string with the field values. Example:
              {"club_society": "Chess Club", "description": "Equipment purchase", ...}
    
    Returns:
        Success or error message.
    """
    file_path = os.path.join(FORMS_DIR, f"{form_id}.json")
    if not os.path.exists(file_path):
        available = [f.replace(".json", "") for f in os.listdir(FORMS_DIR) 
                     if f.endswith(".json") and not f.endswith("_auth.json")]
        return f"Form '{form_id}' not found. Available: {available}. Call list_available_forms() for details."
    
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}. Data must be a valid JSON string."
        
    with open(file_path, "r") as f:
        form_def = FormDefinition.model_validate_json(f.read())
        
    # Try default auth first, then form-specific auth
    auth_file = os.path.join(FORMS_DIR, "default_auth.json")
    if not os.path.exists(auth_file):
        auth_file = os.path.join(FORMS_DIR, f"{form_id}_auth.json")
    
    # Use visible browser so user can see what's happening
    executor = FormExecutor(headless=False)
    await executor.start()
    
    if os.path.exists(auth_file):
        await executor.load_auth(auth_file)
    else:
        await executor.stop()
        return "Authentication not configured. Ask the user to run save_auth.py first."
        
    try:
        await executor.execute(form_def, data_dict)
        # NOTE: We do NOT call executor.stop() here - browser stays open for user to review
        return f"SUCCESS: Form '{form_id}' has been filled. The browser window is open for review. Close it manually when done. The form was NOT submitted."
    except Exception as e:
        await executor.stop()  # Only close on error
        return f"FAILED: {e}"


if __name__ == "__main__":
    mcp.run()
