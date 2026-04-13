"""Processing times commands for COLA Cloud CLI."""

import json

import click

from colacloud_cli.api import APIError, get_client
from colacloud_cli.commands.utils import console, handle_api_error


@click.group(name="processing-times")
def processing_times_group():
    """View TTB processing times for COLAs, formulas, and registrations."""
    pass


@processing_times_group.command(name="list")
@click.option("--commodity", help="Filter by commodity type.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def list_processing_times(commodity: str | None, as_json: bool):
    """List COLA processing times.

    Shows how long it takes TTB to process COLA applications,
    optionally filtered by commodity type.

    Examples:

    \b
        # List all processing times
        cola processing-times list

    \b
        # Filter by commodity
        cola processing-times list --commodity wine
    """
    try:
        with get_client() as client:
            result = client.list_processing_times(commodity=commodity)

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            data = result.get("data", [])
            meta = result.get("meta", {})

            if not data:
                console.print(
                    "[yellow]No processing times found matching your criteria.[/]"
                )
                return

            console.print(json.dumps(data, indent=2))
            total = meta.get("total", len(data))
            console.print(f"\n[dim]{total} result(s)[/]")

    except APIError as e:
        handle_api_error(e)


@processing_times_group.command(name="formula")
@click.option("--formula-type", help="Filter by formula type.")
@click.option("--commodity", help="Filter by commodity type.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def formula_processing_times(
    formula_type: str | None, commodity: str | None, as_json: bool
):
    """List formula processing times.

    Shows how long it takes TTB to process formula applications.

    Examples:

    \b
        # List all formula processing times
        cola processing-times formula

    \b
        # Filter by formula type and commodity
        cola processing-times formula --formula-type domestic --commodity wine
    """
    try:
        with get_client() as client:
            result = client.list_formula_processing_times(
                formula_type=formula_type, commodity=commodity
            )

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            data = result.get("data", [])
            meta = result.get("meta", {})

            if not data:
                console.print(
                    "[yellow]No formula processing times found"
                    " matching your criteria.[/]"
                )
                return

            console.print(json.dumps(data, indent=2))
            total = meta.get("total", len(data))
            console.print(f"\n[dim]{total} result(s)[/]")

    except APIError as e:
        handle_api_error(e)


@processing_times_group.command(name="registration")
@click.option("--category", help="Filter by category.")
@click.option("--application-type", help="Filter by application type.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def registration_processing_times(
    category: str | None, application_type: str | None, as_json: bool
):
    """List registration processing times.

    Shows how long it takes TTB to process registration applications.

    Examples:

    \b
        # List all registration processing times
        cola processing-times registration

    \b
        # Filter by category
        cola processing-times registration --category beverage
    """
    try:
        with get_client() as client:
            result = client.list_registration_processing_times(
                category=category, application_type=application_type
            )

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            data = result.get("data", [])
            meta = result.get("meta", {})

            if not data:
                console.print(
                    "[yellow]No registration processing times found"
                    " matching your criteria.[/]"
                )
                return

            console.print(json.dumps(data, indent=2))
            total = meta.get("total", len(data))
            console.print(f"\n[dim]{total} result(s)[/]")

    except APIError as e:
        handle_api_error(e)
