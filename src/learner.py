from playwright.sync_api import sync_playwright
from google import genai
import json
import os
from .schema import FormDefinition, FormField

class FormLearner:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.client = genai.Client()
        self.model_name = model_name

    def learn(self, url: str, storage_state: str = None) -> FormDefinition:
        """Visits a URL, analyzes the form, and returns a FormDefinition."""
        print(f"Learning form from: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            if storage_state and os.path.exists(storage_state):
                 context = browser.new_context(storage_state=storage_state)
                 print(f"Loaded auth from {storage_state}")
            else:
                 context = browser.new_context()
            
            page = context.new_page()
            page.goto(url)
            page.wait_for_load_state("domcontentloaded")
            
            # Simple heuristic: wait a bit for dynamic forms
            page.wait_for_timeout(2000)

            # Get the accessibility tree - great for understanding structure
            snapshot = page.accessibility.snapshot()
            
            # Get specific form inputs to help map names/ids
            # We execute a script to get a simplified representation of all inputs
            form_elements = page.evaluate("""() => {
                const inputs = Array.from(document.querySelectorAll('input, select, textarea, button'));
                return inputs.map(el => ({
                    tag: el.tagName.toLowerCase(),
                    type: el.type,
                    id: el.id,
                    name: el.name,
                    placeholder: el.placeholder,
                    label: el.labels && el.labels[0] ? el.labels[0].innerText : '',
                    ariaLabel: el.getAttribute('aria-label'),
                    visible: el.offsetParent !== null
                })).filter(el => el.visible);
            }""")

            browser.close()

        # Construct the prompt
        prompt = f"""
        You are an expert at browser automation and HTML analysis.
        I will provide you with information about a web page containing a form.
        Your goal is to create a 'FormDefinition' configuration that describes how to interact with this form.

        URL: {url}

        Here is the simplified list of form elements found on the page:
        {json.dumps(form_elements, indent=2)}

        Here is the accessibility tree snapshot:
        {json.dumps(snapshot, indent=2)}

        Create a JSON object adhering to the following Schema:
        
        class FormField(BaseModel):
            name: str  # Internal key for data (e.g., 'first_name', 'email'). Make these snake_case and intuitive.
            selector: str # reliably unique CSS selector (prefer id, then name, then complex selector)
            type: str # 'text', 'select', 'file', 'click', 'checkbox', 'textarea'
            value: Optional[str] # leave null usually, unless a specific button needs to be clicked
            description: Optional[str] # What this field is for
            required: bool

        class FormDefinition(BaseModel):
            form_id: str # specific specific, e.g. 'ucl_payment_request'
            url: str
            description: str
            login_required: bool
            fields: List[FormField]

        Return ONLY the raw JSON of the FormDefinition.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": FormDefinition,
                },
            )
            return response.parsed
        except Exception as e:
            print(f"Error generating form definition: {e}")
            raise
