"""Shared utilities for COLA Cloud CLI commands."""

import sys

from rich.console import Console

from colacloud_cli.api import APIError, AuthenticationError, RateLimitError

# Shared console instance for all commands
console = Console()


def handle_api_error(e: APIError) -> None:
    """Handle API errors with helpful messages.

    Args:
        e: The API error to handle.

    This function prints a user-friendly error message and exits
    with status code 1.
    """
    if isinstance(e, AuthenticationError):
        console.print(f"[red]Authentication Error:[/] {e.message}")
        console.print("\n[dim]Run 'cola config set-key' to configure your API key,[/]")
        console.print("[dim]or set the COLACLOUD_API_KEY environment variable.[/]")
    elif isinstance(e, RateLimitError):
        console.print(f"[red]Rate Limit Exceeded:[/] {e.message}")
        if e.retry_after:
            console.print(f"[dim]Try again in {e.retry_after} seconds.[/]")
        console.print("\n[dim]Run 'cola usage' to check your API usage.[/]")
    else:
        console.print(f"[red]API Error:[/] {e.message}")
        if e.status_code:
            console.print(f"[dim]Status code: {e.status_code}[/]")
    sys.exit(1)
