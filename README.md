# suu-auto

> [!NOTE]
> **This project is being merged into [`suu-cli`](../suu-cli).** The form filler now lives
> there as `suu forms …`, `suu mcp …`, and `suu poll`, alongside the data scraper, in one
> install. Notable changes in suu-cli: the MCP server is started with `suu mcp run` (and
> `suu mcp setup` auto-configures your AI apps); logins are saved under `~/.suu` instead of
> `forms/` or `~/.suu-auto`. This repo stays as the reference until `suu-cli` is fully
> verified, then will be archived.

UCL Student Union form automation — run as an **MCP server** for Claude Desktop or as a **polling worker** for the receipt-gatherer web app.

Not affiliated with UCL or the Students' Union UCL.

## Modes

| Command | Description |
| :--- | :--- |
| `suu-auto mcp` | MCP server — Claude calls tools to fill forms interactively |
| `suu-auto poll` | Polling worker — reads queued jobs from the receipt-gatherer API and fills forms automatically |

Both modes use the same `FormExecutor` engine under the hood. The form is **never submitted automatically** — the browser stays open for review.

## Supported Forms

| Form ID | Description | Use Case |
| :--- | :--- | :--- |
| `payment_request` | **Payment Request Form** | Reimbursements (paying back a member). Do NOT use for invoices. |
| `purchase_request` | **Purchase Request Form** | Paying invoices to suppliers or asking the Union to buy something. |

## Installation

```bash
git clone <repo_url> suu-auto
cd suu-auto
pip install -e .
playwright install chromium
```

## Authentication

> [!WARNING]
> **Never commit `auth.json` files.** They contain live session cookies. The `.gitignore` excludes `forms/*_auth.json`.

Save your session once (opens a browser for manual login):

```bash
python scripts/save_auth.py
```

This writes `forms/default_auth.json` (MCP mode) or `~/.suu-auto/auth.json` (poll mode).

## MCP mode — Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "suu-auto": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/suu-auto",
        "run",
        "suu-auto",
        "mcp"
      ]
    }
  }
}
```

Claude will call `list_available_forms()` then `run_form_automation(form_id, data)`.

## Poll mode — receipt-gatherer integration

Configure `.env`:

```env
APP_URL=https://your-receipt-gatherer-app.example.com
WORKER_AUTH_TOKEN=your-shared-secret          # must match the server's WORKER_AUTH_TOKEN
SUU_AUTO_HOME=~/.suu-auto                     # optional, default shown
WORKER_DEFAULT_FORM_ID=payment_request        # optional, default shown
AUTH_MAX_AGE_DAYS=7                           # optional; rejects stale auth.json
WORKER_POLL_INTERVAL_SECONDS=5                # optional
WORKER_HEARTBEAT_INTERVAL_SECONDS=15          # optional
```

Then run:

```bash
suu-auto poll
```

The worker claims jobs from `/api/worker/poll`, downloads the receipt image, fills the form, and reports done/failed. The job payload's `form_id` field selects which form to fill; it defaults to `payment_request`.

## Running a form manually

```bash
python scripts/run_form.py payment_request --data examples/my_data.json
python scripts/run_form.py purchase_request --data examples/my_data.json
```

## Recording a new form

```bash
python scripts/record_form_def.py "https://studentsunionucl.org/forms/your-form" --id new_form_id
```

## Project structure

```
src/
  cli.py        Entry point — dispatches to mcp or poll
  server.py     MCP server (FastMCP tools)
  worker.py     Polling worker loop
  payload.py    Maps receipt-gatherer job payload → form field data
  executor.py   Playwright form automation engine
  schema.py     Pydantic models (FormDefinition, FormField)
  recorder.py   Interactive form recorder
forms/
  payment_request.json
  purchase_request.json
scripts/
  save_auth.py          Save browser session (one-time login)
  run_form.py           Run a form manually from the CLI
  record_form_def.py    Record a new form definition interactively
```
