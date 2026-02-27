"""
SUU-MCP Package
"""
# Expose key classes for easier imports
from .schema import FormDefinition, FormField
from .executor import FormExecutor
from .recorder import FormRecorder

# Note: FormLearner is not exported as it requires optional dependencies (google-genai)
# Import it directly if needed: from src.learner import FormLearner
