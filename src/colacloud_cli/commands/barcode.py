"""Barcode lookup command for COLA Cloud CLI."""

import json
import sys

import click
from rich.console import Console

from colacloud_cli.api import APIError, AuthenticationError, RateLimitError, get_client
from colacloud_cli.formatters import format_barcode_result

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
        console.print("\n[dim]Run 'cola usage' to check your API usage.[/]")
    else:
        console.print(f"[red]API Error:[/] {e.message}")
        if e.status_code:
            console.print(f"[dim]Status code: {e.status_code}[/]")
    sys.exit(1)


@click.command(name="barcode")
@click.argument("value")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def barcode_command(value: str, as_json: bool):
    """Look up COLAs by barcode (UPC, EAN, etc.).

    VALUE is the barcode number from the product label.

    This command searches the COLA database for products that have been
    registered with the specified barcode.

    Examples:

    \b
        # Look up a UPC barcode
        cola barcode 012345678901

    \b
        # Look up an EAN barcode
        cola barcode 5000281025155

    \b
        # Output as JSON
        cola barcode 012345678901 --json
    """
    try:
        with get_client() as client:
            result = client.lookup_barcode(value)

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            data = result.get("data", {})
            format_barcode_result(data, console)

    except APIError as e:
        handle_api_error(e)
