import argparse
import sys
import os
import re
from src.learner import FormLearner
from src.schema import FormDefinition

def slugify(text: str) -> str:
    """Converts a string to a safe filename slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    text = text.strip('_')
    return text

def main():
    parser = argparse.ArgumentParser(description="Learn a form definition from a URL.")
    parser.add_argument("url", help="The URL of the form to learn")
    parser.add_argument("--id", help="The ID for the form definition. Defaults to slug generated from URL.")
    parser.add_argument("--output", help="Path to save the JSON file. Defaults to forms/<id>.json")
    parser.add_argument("--model", default="gemini-2.0-flash-exp", help="Gemini model to use (default: gemini-2.0-flash-exp)")

    args = parser.parse_args()

    # Determine Form ID
    if args.id:
        form_id = args.id
    else:
        # Simple heuristic: last part of path or host
        form_id = slugify(args.url.split('?')[0].split('/')[-1] or args.url.split('//')[1].split('/')[0])
        if not form_id:
            form_id = "unknown_form"
        print(f"Auto-generated ID: {form_id}")

    # Determine Output Path
    if args.output:
        output_path = args.output
    else:
        forms_dir = os.path.join(os.getcwd(), 'forms')
        os.makedirs(forms_dir, exist_ok=True)
        output_path = os.path.join(forms_dir, f"{form_id}.json")

    print(f"Learning form from: {args.url}")
    print(f"Model: {args.model}")
    
    learner = FormLearner(model_name=args.model)
    
    try:
        form_def = learner.learn(args.url)
        
        # Override ID if passed in args to ensure consistency
        if args.id:
             form_def.form_id = args.id
        # Else ensure the learned ID is reasonable or use our generated one if the AI gives garbage?
        # Actually better to trust the AI but maybe warn if different.
        # For now, let's inject the ID we decided on if the AI's is empty or generic
        if not form_def.form_id or form_def.form_id == "form_id":
            form_def.form_id = form_id

        # Save to file
        with open(output_path, "w") as f:
            f.write(form_def.model_dump_json(indent=4))
            
        print(f"Successfully saved form definition to: {output_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
