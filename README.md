# SUU MCP Server

A robust Model Context Protocol (MCP) server for automating forms at UCL Students' Union (https://studentsunionucl.org). Built with Playwright and FastMCP.

## Features

- **Form Automation**: Record and replay form interactions (typing, clicking, file uploads) for complex Drupal forms.
- **Smart Inference**: Automatically infers defaults for common fields (e.g., "Grand/Non-grant", "Payment Method") if data is missing, reducing the need for user prompts.
- **Secure**: Authentication sessions (cookies) are saved locally and never shared. Sensitive files aregitignored.
- **Robustness**: Handles styling quirks (hidden file inputs), conditional visibility, and AJAX uploads with auto-retry logic.

## Supported Forms

| Form ID | Description | Use Case |
| :--- | :--- | :--- |
| `purchase_request` | **Purchase Request Form** | Request the Union to buy something for you (they pay supplier directly). |
| `payment_request` | **Payment Request Form** | Request reimbursement (pay back a member) or pay an invoice via Bank Transfer. |

## Installation

1. **Clone and Install**:
   ```bash
   git clone <repo_url>
   cd suu-mcp
   pip install -e .
   ```

2. **Install Playwright Browsers**:
   ```bash
   playwright install chromium
   ```

## Security & Authentication

> [!WARNING]
> **Never commit your `auth.json` files.** They contain live session cookies. The `.gitignore` is configured to exclude `forms/*_auth.json`.

1. **Login**:
   Run the auth script to log in interactively. This captures your session cookies to `forms/default_auth.json`.
   ```bash
   python scripts/save_auth.py
   ```

## Usage

### 1. Run a Form (Dry Run)
You can run a form automation in "review mode" (no submission) to verify it works.

**Purchase Request:**
```bash
python scripts/run_form.py purchase_request --data examples/my_test_data.json
```

**Payment Request:**
```bash
python scripts/run_form.py payment_request --data examples/test_payment_data.json
```

### 2. Smart Inference
The system is designed to be "smart". You don't need to provide every single field.
*   **Missing Payment Method?** Defaults to "UK Bank Transfer".
*   **Missing Grant Status?** Defaults to "Non-grant".
*   **Summarization**: You can provide a single cost item summarizing multiple small expenses from the same invoice.

### 3. Record a New Form
To teach the system a new form:
```bash
python scripts/record_form_def.py "https://studentsunionucl.org/forms/your-form-url" --id new_form_id
```

## Project Structure

*   `src/`: Core logic (`server`, `executor`, `schema`).
*   `forms/`: Form definitions (`.json`) and auth files.
*   `scripts/`: Utility scripts for running, recording, and debugging.
*   `examples/`: Example data files and assets (receipts/invoices).

## Claude Desktop Configuration

To use this with Claude Desktop, add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "suu-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/suu-mcp",
        "run",
        "suu-mcp"
      ]
    }
  }
}
```
*(Replace `/absolute/path/to/suu-mcp` with your actual path).*
