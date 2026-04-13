"""Production reports commands for COLA Cloud CLI."""

import json

import click

from colacloud_cli.api import APIError, get_client
from colacloud_cli.commands.utils import console, handle_api_error


@click.group(name="production-reports")
def production_reports_group():
    """View TTB production reports and statistics."""
    pass


@production_reports_group.command(name="list")
@click.option("--commodity", help="Filter by commodity type.")
@click.option("--year", type=int, help="Filter by year.")
@click.option("--month", type=int, help="Filter by month (1-12).")
@click.option("--report-type", help="Filter by report type.")
@click.option("--statistical-group", help="Filter by statistical group.")
@click.option(
    "--limit", "per_page", default=100, type=int, help="Results per page (max 100)."
)
@click.option("--page", default=1, type=int, help="Page number.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def list_production_reports(
    commodity: str | None,
    year: int | None,
    month: int | None,
    report_type: str | None,
    statistical_group: str | None,
    per_page: int,
    page: int,
    as_json: bool,
):
    """List production reports.

    Browse TTB production report data with optional filters.

    Examples:

    \b
        # List all production reports
        cola production-reports list

    \b
        # Filter by commodity and year
        cola production-reports list --commodity wine --year 2024

    \b
        # Filter by month
        cola production-reports list --year 2024 --month 6
    """
    try:
        with get_client() as client:
            result = client.list_production_reports(
                commodity=commodity,
                year=year,
                month=month,
                report_type=report_type,
                statistical_group=statistical_group,
                page=page,
                per_page=min(per_page, 100),
            )

        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            data = result.get("data", [])
            meta = result.get("meta", {})

            if not data:
                console.print(
                    "[yellow]No production reports found matching your criteria.[/]"
                )
                return

            console.print(json.dumps(data, indent=2))
            total = meta.get("total", len(data))
            page_num = meta.get("page", page)
            has_more = meta.get("has_more", False)
            console.print(f"\n[dim]{total} total result(s), page {page_num}[/]")
            if has_more:
                console.print("[dim]More results available. Use --page to paginate.[/]")

    except APIError as e:
        handle_api_error(e)
