from playwright.sync_api import sync_playwright
from .schema import FormDefinition, FormField, FormStep
from typing import List, Dict, Any
import json
import time
import os

class FormRecorder:
    def __init__(self):
        self.interactions = []
        self.url = ""

    def record(self, url: str, storage_state: str = None) -> FormDefinition:
        """Opens a browser, records interactions, and returns a FormDefinition."""
        self.url = url
        self.interactions = []

        with sync_playwright() as p:
            # Headful mode so user can see what they are doing
            browser = p.chromium.launch(headless=False)
            
            if storage_state and os.path.exists(storage_state):
                 print(f"Loading auth from {storage_state}")
                 context = browser.new_context(storage_state=storage_state)
            else:
                 context = browser.new_context()
            
            # Expose function to capture events from JS
            def on_interaction(data):
                # Filter out duplicate interactions on the same field unless value changed?
                # For now, just append everything, we clean up later
                print(f"Captured interaction: {data['type']} on {data['selector']}")
                self.interactions.append(data)

            context.expose_binding("recordInteraction", lambda source, data: on_interaction(data))
            
            page = context.new_page()
            
            # Inject script to listen to events
            init_script = """
                document.addEventListener('DOMContentLoaded', () => {
                    const notify = (eventType, target) => {
                        if (!target) return;
                        
                        // Heuristic for selector: ID > Name > Data Attributes > CSS Path
                        let selector = '';
                        if (target.id) {
                            selector = '#' + target.id;
                        } else if (target.name) {
                            selector = `[name="${target.name}"]`;
                        } else if (target.hasAttribute('data-drupal-selector')) {
                            selector = `[data-drupal-selector="${target.getAttribute('data-drupal-selector')}"]`;
                        } else {
                            // Simple fallback - unique path?
                            // This is a weak spot, but good enough for simple forms
                             selector = target.tagName.toLowerCase();
                             if (target.type) selector += `[type="${target.type}"]`;
                             // Add classes if available
                             if (target.className) selector += `.${target.className.split(' ').join('.')}`;
                        }

                        window.recordInteraction({
                            type: eventType,
                            tagName: target.tagName.toLowerCase(),
                            inputType: target.type || null,
                            selector: selector,
                            name: target.name || target.id || '',
                            value: target.value || '',
                            label: target.labels && target.labels[0] ? target.labels[0].innerText : '',
                            options: target.tagName.toLowerCase() === 'select' ? Array.from(target.options).map(o => o.text) : null
                        });
                    };

                    document.addEventListener('change', (e) => notify('change', e.target), true);
                    document.addEventListener('click', (e) => {
                        // Capture clicks on buttons or elements acting as buttons
                        const btn = e.target.closest('button, input[type="submit"], input[type="button"], [role="button"]');
                        if (btn) {
                             notify('click', btn);
                        }
                    }, true);
                });
            """
            # Note: We commented out click for now to focus on data entry, but 'submit' buttons are important.
            # Let's refinements: mainly want 'change' for inputs, 'click' for buttons.
            
            page.add_init_script(init_script) 
            
            print(f"Opening {url}...")
            print("Interact with the form. When finished, CLOSE THE BROWSER WINDOW to save.")
            
            page.goto(url)
            
            # Wait for browser to close
            try:
                page.wait_for_event("close", timeout=0) # 0 = infinite timeout
            except Exception as e:
                pass # Browser closed
                
            browser.close()

        return self._process_interactions()

    def _process_interactions(self) -> FormDefinition:
        """Converts raw interactions into a clean FormDefinition."""
        fields: List[FormField] = []
        seen_selectors = set()

        for interaction in self.interactions:
            selector = interaction['selector']
            
            # Skip if we already have a definition for this field
            # (In a real recorder, we might want to update the value, but for definition generation, first capture is fine usually)
            if selector in seen_selectors:
                continue

            field_type = 'text' # Default
            if interaction['type'] == 'click':
                field_type = 'click'
            elif interaction['tagName'] == 'select':
                field_type = 'select'
            elif interaction['inputType'] == 'checkbox':
                field_type = 'checkbox'
            elif interaction['inputType'] == 'file':
                field_type = 'file'
            elif interaction['tagName'] == 'textarea':
                field_type = 'textarea'
            
            # Variable name: prioritization
            name = interaction['name']
            if not name:
                # Fallback to label
                name = interaction['label'].lower().replace(' ', '_')
            if not name:
                # Fallback to selector hash or similar?
                name = f"field_{len(fields) + 1}"

            is_submit = False
            if interaction['inputType'] == 'submit' or (interaction['type'] == 'click' and interaction['tagName'] == 'button' and 'submit' in (interaction.get('innerText', '') or '').lower()):
                 is_submit = True
                 
            fields.append(FormField(
                name=name,
                selector=selector,
                type=field_type,
                value=None, 
                description=interaction['label'] or f"Input for {name}",
                required=False,
                is_submit=is_submit,
                options=interaction.get('options')
            ))
            seen_selectors.add(selector)

        return FormDefinition(
            form_id="generated_form", # Placeholder, caller should set
            url=self.url,
            description="Recorded form definition",
            fields=fields
        )
