from playwright.sync_api import sync_playwright
import os

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="forms/default_auth.json") if os.path.exists("forms/default_auth.json") else browser.new_context()
        page = context.new_page()
        page.goto("https://studentsunionucl.org/forms/purchase-request-form")
        
        print("Loading page...")
        page.wait_for_load_state("domcontentloaded")
        
        print("\n--- VISIBLE INPUTS ---")
        inputs = page.locator("input[type='radio']").all()
        for i in inputs:
            try:
                id_attr = i.get_attribute("id") or ""
                name_attr = i.get_attribute("name") or ""
                val = i.get_attribute("value") or ""
                drupal_attr = i.get_attribute("data-drupal-selector") or ""
                label = ""
                # Try to find label
                if id_attr:
                    l = page.locator(f"label[for='{id_attr}']")
                    if l.count() > 0:
                        label = l.first.inner_text()
                
                print(f"Label: {label} | ID: {id_attr} | Name: {name_attr} | Value: {val} | Drupal: {drupal_attr}")
            except:
                pass
                
        print("\n--- END ---")
        # input("Press Enter to close...")
        browser.close()

if __name__ == "__main__":
    inspect()
