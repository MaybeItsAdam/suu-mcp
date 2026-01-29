import argparse
import asyncio
import json
import os
import sys
from src.schema import FormDefinition
from src.executor import FormExecutor


async def run_form(form_def: FormDefinition, data: dict, auth_file: str = None):
    """Async form execution function."""
    executor = FormExecutor(headless=False)
    
    try:
        await executor.start()
        
        if auth_file:
            print(f"Loading auth from {auth_file}")
            await executor.load_auth(auth_file)
            
        await executor.execute(form_def, data)
        
        print("Execution completed.")
        print("Press Enter to close browser...")
        input()
        
    except Exception as e:
        print(f"Error during execution: {e}", file=sys.stderr)
    finally:
        await executor.stop()


def main():
    parser = argparse.ArgumentParser(description="Run a learned form definition.")
    parser.add_argument("form_id", help="The ID of the form to run (or path to json file).")
    parser.add_argument("--data", help="Path to a JSON file containing form data.")
    parser.add_argument("--auth", help="Path to a specific auth.json file to use.")
    # Note: --submit flag removed. Forms are NEVER submitted.
    
    args = parser.parse_args()
    
    # Locate form definition
    if os.path.exists(args.form_id):
        form_path = args.form_id
    else:
        # Check in local forms dir
        form_path = os.path.join("forms", f"{args.form_id}.json")
        if not os.path.exists(form_path):
            if os.path.exists(f"{args.form_id}.json"):
                form_path = f"{args.form_id}.json"
            else:
                print(f"Error: Form definition not found for '{args.form_id}'. Checked {form_path}", file=sys.stderr)
                sys.exit(1)

    try:
        with open(form_path, "r") as f:
            form_def = FormDefinition.model_validate_json(f.read())
    except Exception as e:
        print(f"Error loading form definition: {e}", file=sys.stderr)
        sys.exit(1)

    # Load data
    data = {}
    if args.data:
        try:
            with open(args.data, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading data file: {e}", file=sys.stderr)
            sys.exit(1)

    # Prompt for missing data
    print(f"Running form: {form_def.form_id} ({form_def.url})")
    print("NOTE: Form will NOT be submitted (review mode only)")
    print("------------------------------------------------")
    
    for field in form_def.fields:
        if field.type == 'click':
            continue
             
        if field.name not in data and field.required:
            prompt = f"Enter value for '{field.name}'"
            if field.description:
                prompt += f" ({field.description})"
            prompt += ": "
            
            try:
                val = input(prompt)
                if val.strip():
                    data[field.name] = val
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                sys.exit(1)
                
    print("\nStarting execution...")
    
    # Determine auth file
    auth_file = None
    
    if args.auth:
        if os.path.exists(args.auth):
            auth_file = args.auth
        else:
            print(f"Warning: Specified auth file '{args.auth}' not found.", file=sys.stderr)

    if not auth_file:
        base_name = os.path.splitext(os.path.basename(form_path))[0]
        specific_auth = os.path.join(os.path.dirname(form_path), f"{base_name}_auth.json")
        default_auth = os.path.join(os.path.dirname(form_path), "default_auth.json")
        
        if os.path.exists(specific_auth) and os.path.exists(default_auth):
            specific_mtime = os.path.getmtime(specific_auth)
            default_mtime = os.path.getmtime(default_auth)
            if default_mtime > specific_mtime:
                print(f"Auto-selecting 'default_auth.json' because it is newer.")
                auth_file = default_auth
            else:
                auth_file = specific_auth
        elif os.path.exists(specific_auth):
            auth_file = specific_auth
        elif os.path.exists(default_auth):
            auth_file = default_auth

    # Run async
    asyncio.run(run_form(form_def, data, auth_file))


if __name__ == "__main__":
    main()
