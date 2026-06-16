"""
Entry point for the suu-auto command.

    suu-auto mcp    Run as an MCP server (for Claude Desktop / any MCP client)
    suu-auto poll   Run as a polling worker against the receipt-gatherer API
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="suu-auto",
        description="UCL Student Union form automation.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "mcp",
        help="Run as an MCP server (for use with Claude Desktop or any MCP client).",
    )
    sub.add_parser(
        "poll",
        help=(
            "Run as a polling worker. Reads jobs from the receipt-gatherer API "
            "and fills the SU form using Playwright."
        ),
    )

    args = parser.parse_args()

    if args.command == "mcp":
        from .server import mcp
        mcp.run()

    elif args.command == "poll":
        import asyncio
        from .worker import run_worker
        asyncio.run(run_worker())

    else:
        parser.print_help()
        sys.exit(1)
