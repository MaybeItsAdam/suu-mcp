import argparse
import sys
import os
import re
from src.recorder import FormRecorder

def slugify(text: str) -> str:
    """Converts a string to a safe filename slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    text = text.strip('_')
    return text

def main():
    parser = argparse.ArgumentParser(
        description="Record a form definition by demonstrating.",
        usage="%(prog)s <form_id> <url>  OR  %(prog)s <url> --id <form_id>"
    )
    parser.add_argument("first_arg", help="Form ID or URL")
    parser.add_argument("second_arg", nargs="?", help="URL (if first arg is form ID)")
    parser.add_argument("--id", help="Form ID (if first arg is URL)")
    parser.add_argument("--output", help="Path to save the JSON file. Defaults to forms/<id>.json")
    parser.add_argument("--auth", help="Path to auth.json file.")

    args = parser.parse_args()
    
    # Determine if first_arg is URL or form_id
    if args.first_arg.startswith("http"):
        # First arg is URL
        url = args.first_arg
        form_id = args.id
    elif args.second_arg and args.second_arg.startswith("http"):
        # First arg is form_id, second is URL
        form_id = args.first_arg
        url = args.second_arg
    else:
        print("Error: Please provide a URL. Usage:")
        print("  python record_form_def.py <form_id> <url>")
        print("  python record_form_def.py <url> --id <form_id>")
        sys.exit(1)

    # Determine Form ID if not already set
    if not form_id:
        # Simple heuristic from URL
        form_id = slugify(url.split('?')[0].split('/')[-1] or url.split('//')[1].split('/')[0])
        if not form_id:
            form_id = "recorded_form"
        print(f"Auto-generated ID: {form_id}")

    # Determine Output Path
    if args.output:
        output_path = args.output
    else:
        forms_dir = os.path.join(os.getcwd(), 'forms')
        os.makedirs(forms_dir, exist_ok=True)
        output_path = os.path.join(forms_dir, f"{form_id}.json")

    # Determine Auth Path
    auth_path = None
    if args.auth:
        auth_path = args.auth
    else:
        possible_auth = os.path.join(os.path.dirname(output_path), f"{form_id}_auth.json")
        if os.path.exists(possible_auth):
            auth_path = possible_auth
            print(f"Auto-detected auth file: {auth_path}")
        else:
            default_auth = os.path.join(os.path.dirname(output_path), "default_auth.json")
            if os.path.exists(default_auth):
                auth_path = default_auth
                print(f"Auto-detected default auth file: {auth_path}")

    recorder = FormRecorder()
    
    try:
        print(f"Launching recorder for: {url}")
        form_def = recorder.record(url, storage_state=auth_path)
        
        form_def.form_id = form_id
        
        # Save to file
        with open(output_path, "w") as f:
            f.write(form_def.model_dump_json(indent=4))
            
        print(f"Successfully recorded and saved form definition to: {output_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
