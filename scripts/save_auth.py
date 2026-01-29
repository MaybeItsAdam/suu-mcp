import argparse
import os
import sys
from playwright.sync_api import sync_playwright

def main():
    parser = argparse.ArgumentParser(description="Authenticate and save session state.")
    parser.add_argument("id", nargs='?', default="default", help="The ID for the form/site (saves to forms/<id>_auth.json)")
    parser.add_argument("--url", help="The login URL. If not provided, tries to find it from forms/<id>.json, otherwise opens blank page.")
    
    args = parser.parse_args()
    
    forms_dir = os.path.join(os.getcwd(), 'forms')
    os.makedirs(forms_dir, exist_ok=True)
    auth_file = os.path.join(forms_dir, f"{args.id}_auth.json")
    
    url = args.url
    if not url:
        # Try to find existing definition
        def_file = os.path.join(forms_dir, f"{args.id}.json")
        if os.path.exists(def_file):
            import json
            try:
                with open(def_file, 'r') as f:
                    data = json.load(f)
                    url = data.get('url')
                    print(f"Found URL from existing definition: {url}")
            except:
                pass
    
    if not url:
        url = "about:blank" 
        print("No URL provided or found. Opening browser (please navigate to login page)...")

    with sync_playwright() as p:
        print(f"Launching browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(url)
        
        print("----------------------------------------------------------------")
        print("Please log in in the opened browser window.")
        print("When you are successfully logged in, CLOSE THE BROWSER WINDOW.")
        print("----------------------------------------------------------------")

        # Wait for browser to close
        try:
            page.wait_for_event("close", timeout=0)
        except KeyboardInterrupt:
            print("\nReceived Ctrl+C. Saving session state...")
        except Exception:
            pass # Browser closed
            
        # Save state
        try:
            context.storage_state(path=auth_file)
            print(f"Session state saved to: {auth_file}")
        except Exception as e:
             print(f"Error saving state (did you close the entire browser too fast?): {e}")

        browser.close()

if __name__ == "__main__":
    main()
