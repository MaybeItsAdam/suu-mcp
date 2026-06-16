"""
suu-auto — UCL Student Union form automation.

suu-auto is a pure executor: it receives pre-formatted data and fills forms
using Playwright. It makes no AI calls. Intelligence lives in the caller
(Claude via MCP, or the receipt-gatherer's Groq autofill).
"""

from .schema import FormDefinition, FormField
from .executor import FormExecutor
from .recorder import FormRecorder

# Note: FormLearner is not exported as it requires optional dependencies (google-genai)
# Import it directly if needed: from src.learner import FormLearner
