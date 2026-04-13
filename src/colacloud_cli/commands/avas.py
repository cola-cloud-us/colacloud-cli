"""AVA commands for COLA Cloud CLI."""

import json

import click

from colacloud_cli.api import APIError, get_client
from colacloud_cli.commands.utils import console, handle_api_error


@click.group(name="avas")
def avas_group():
    """Browse American Viticultural Areas (AVAs)."""
    pass


@avas_group.command(name="list")
@click.option("--state", help="Filter by state (e.g., CA, OR, WA).")
@click.option("-q", "--query", help="Search by AVA name.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def list_avas(state: str | None, query: str | None, as_json: bool):
    """List American Viticultural Areas.

    Browse and search federally recognized wine grape-growing regions.

    Examples:

    \b
        # List all AVAs
        cola avas list

    \b
        # Filter by state
        cola avas list --state CA

    \b
        # Search by name
        cola avas list -q "napa"
    """
    try:
        with get_client() as client:
            result = client.list_avas(state=state, query=query)

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            data = result.get("data", [])
            meta = result.get("meta", {})

            if not data:
                console.print("[yellow]No AVAs found matching your criteria.[/]")
                return

            console.print(json.dumps(data, indent=2))
            total = meta.get("total", len(data))
            console.print(f"\n[dim]{total} result(s)[/]")

    except APIError as e:
        handle_api_error(e)


@avas_group.command(name="get")
@click.argument("ava_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def get_ava(ava_id: str, as_json: bool):
    """Get detailed information about a specific AVA.

    AVA_ID is the unique identifier for the American Viticultural Area.

    Examples:

    \b
        # Get AVA details
        cola avas get napa-valley

    \b
        # Output as JSON
        cola avas get napa-valley --json
    """
    try:
        with get_client() as client:
            result = client.get_ava(ava_id)

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            data = result.get("data", {})
            console.print(json.dumps(data, indent=2))

    except APIError as e:
        handle_api_error(e)
