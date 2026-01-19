"""Usage command for COLA Cloud CLI."""

import json
import sys

import click
from rich.console import Console

from colacloud_cli.api import APIError, AuthenticationError, RateLimitError, get_client
from colacloud_cli.formatters import format_usage

console = Console()


def handle_api_error(e: APIError) -> None:
    """Handle API errors with helpful messages."""
    if isinstance(e, AuthenticationError):
        console.print(f"[red]Authentication Error:[/] {e.message}")
        console.print("\n[dim]Run 'cola config set-key' to configure your API key,[/]")
        console.print("[dim]or set the COLACLOUD_API_KEY environment variable.[/]")
    elif isinstance(e, RateLimitError):
        console.print(f"[red]Rate Limit Exceeded:[/] {e.message}")
        if e.retry_after:
            console.print(f"[dim]Try again in {e.retry_after} seconds.[/]")
    else:
        console.print(f"[red]API Error:[/] {e.message}")
        if e.status_code:
            console.print(f"[dim]Status code: {e.status_code}[/]")
    sys.exit(1)


@click.command(name="usage")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def usage_command(as_json: bool):
    """Show your API usage statistics.

    Displays your current API tier, monthly request limit,
    how many requests you've used this period, and your
    per-minute rate limit.

    Examples:

    \b
        # Show usage stats
        cola usage

    \b
        # Output as JSON
        cola usage --json
    """
    try:
        with get_client() as client:
            result = client.get_usage()

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            data = result.get("data", {})
            format_usage(data, console)

    except APIError as e:
        handle_api_error(e)
