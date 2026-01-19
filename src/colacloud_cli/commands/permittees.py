"""Permittee commands for COLA Cloud CLI."""

import json
import sys

import click
from rich.console import Console

from colacloud_cli.api import APIError, AuthenticationError, RateLimitError, get_client
from colacloud_cli.formatters import (
    format_pagination,
    format_permittee_detail,
    format_permittee_table,
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


@click.group(name="permittees")
def permittees_group():
    """Search and retrieve permittee records."""
    pass


@permittees_group.command(name="list")
@click.option("-q", "--query", help="Search by company name (partial match).")
@click.option("--state", help="Filter by state (e.g., CA, NY, TX).")
@click.option("--active/--inactive", default=None, help="Filter by active status.")
@click.option("--limit", "per_page", default=20, type=int, help="Results per page (max 100).")
@click.option("--page", default=1, type=int, help="Page number.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def list_permittees(
    query: str | None,
    state: str | None,
    active: bool | None,
    per_page: int,
    page: int,
    as_json: bool,
):
    """List and search permittees (alcohol producers/importers).

    Examples:

    \b
        # Search by company name
        cola permittees list -q "diageo"

    \b
        # List active permittees in California
        cola permittees list --state CA --active

    \b
        # List all permittees in Kentucky
        cola permittees list --state KY
    """
    try:
        with get_client() as client:
            result = client.list_permittees(
                query=query,
                state=state,
                is_active=active,
                page=page,
                per_page=min(per_page, 100),
            )

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            permittees = result.get("data", [])
            pagination = result.get("pagination", {})

            if not permittees:
                console.print("[yellow]No permittees found matching your criteria.[/]")
                return

            table = format_permittee_table(permittees, console)
            console.print(table)
            format_pagination(pagination, console)

    except APIError as e:
        handle_api_error(e)


@permittees_group.command(name="get")
@click.argument("permit_number")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def get_permittee(permit_number: str, as_json: bool):
    """Get detailed information about a specific permittee.

    PERMIT_NUMBER is the TTB permit number (e.g., NY-I-136).

    Examples:

    \b
        # Get permittee details
        cola permittees get NY-I-136

    \b
        # Output as JSON
        cola permittees get NY-I-136 --json
    """
    try:
        with get_client() as client:
            result = client.get_permittee(permit_number)

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            permittee = result.get("data", {})
            format_permittee_detail(permittee, console)

    except APIError as e:
        handle_api_error(e)
