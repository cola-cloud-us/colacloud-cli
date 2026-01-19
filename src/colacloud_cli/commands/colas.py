"""COLA commands for COLA Cloud CLI."""

import json
import sys

import click
from rich.console import Console

from colacloud_cli.api import APIError, AuthenticationError, RateLimitError, get_client
from colacloud_cli.formatters import (
    format_cola_detail,
    format_cola_table,
    format_pagination,
)

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


@click.group(name="colas")
def colas_group():
    """Search and retrieve COLA records."""
    pass


@colas_group.command(name="list")
@click.option("-q", "--query", help="Full-text search query.")
@click.option(
    "--product-type",
    type=click.Choice(["malt beverage", "wine", "distilled spirits"], case_sensitive=False),
    help="Filter by product type.",
)
@click.option("--origin", help="Filter by origin (country/state).")
@click.option("--brand", "brand_name", help="Filter by brand name (partial match).")
@click.option("--date-from", "approval_date_from", help="Filter by minimum approval date (YYYY-MM-DD).")
@click.option("--date-to", "approval_date_to", help="Filter by maximum approval date (YYYY-MM-DD).")
@click.option("--abv-min", type=float, help="Filter by minimum ABV.")
@click.option("--abv-max", type=float, help="Filter by maximum ABV.")
@click.option("--limit", "per_page", default=20, type=int, help="Results per page (max 100).")
@click.option("--page", default=1, type=int, help="Page number.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def list_colas(
    query: str | None,
    product_type: str | None,
    origin: str | None,
    brand_name: str | None,
    approval_date_from: str | None,
    approval_date_to: str | None,
    abv_min: float | None,
    abv_max: float | None,
    per_page: int,
    page: int,
    as_json: bool,
):
    """List and search COLA records.

    Examples:

    \b
        # Search for bourbon
        cola colas list -q "bourbon"

    \b
        # List wines from California
        cola colas list --product-type wine --origin california

    \b
        # Find high-ABV spirits
        cola colas list --product-type "distilled spirits" --abv-min 50

    \b
        # Search by brand
        cola colas list --brand "buffalo trace"
    """
    try:
        with get_client() as client:
            result = client.list_colas(
                query=query,
                product_type=product_type,
                origin=origin,
                brand_name=brand_name,
                approval_date_from=approval_date_from,
                approval_date_to=approval_date_to,
                abv_min=abv_min,
                abv_max=abv_max,
                page=page,
                per_page=min(per_page, 100),
            )

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            colas = result.get("data", [])
            pagination = result.get("pagination", {})

            if not colas:
                console.print("[yellow]No COLAs found matching your criteria.[/]")
                return

            table = format_cola_table(colas, console)
            console.print(table)
            format_pagination(pagination, console)

    except APIError as e:
        handle_api_error(e)


@colas_group.command(name="get")
@click.argument("ttb_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def get_cola(ttb_id: str, as_json: bool):
    """Get detailed information about a specific COLA.

    TTB_ID is the unique identifier for the COLA (e.g., 24001234).

    Examples:

    \b
        # Get COLA details
        cola colas get 24001234

    \b
        # Output as JSON
        cola colas get 24001234 --json
    """
    try:
        with get_client() as client:
            result = client.get_cola(ttb_id)

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            cola = result.get("data", {})
            format_cola_detail(cola, console)

    except APIError as e:
        handle_api_error(e)


@colas_group.command(name="search")
@click.argument("query")
@click.option("--limit", "per_page", default=20, type=int, help="Results per page (max 100).")
@click.option("--page", default=1, type=int, help="Page number.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def search_colas(query: str, per_page: int, page: int, as_json: bool):
    """Quick search for COLAs.

    This is a shortcut for 'cola colas list -q <query>'.

    Examples:

    \b
        # Search for whiskey
        cola colas search "whiskey"

    \b
        # Search for a specific brand
        cola colas search "buffalo trace"
    """
    try:
        with get_client() as client:
            result = client.list_colas(
                query=query,
                page=page,
                per_page=min(per_page, 100),
            )

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            colas = result.get("data", [])
            pagination = result.get("pagination", {})

            if not colas:
                console.print(f"[yellow]No COLAs found for '{query}'.[/]")
                return

            table = format_cola_table(colas, console)
            console.print(table)
            format_pagination(pagination, console)

    except APIError as e:
        handle_api_error(e)
