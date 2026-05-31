"""COLA commands for COLA Cloud CLI."""

import json

import click

from colacloud_cli.api import APIError, get_client
from colacloud_cli.commands.utils import console, handle_api_error
from colacloud_cli.formatters import (
    format_cola_detail,
    format_cola_table,
    format_pagination,
)


def _join_multi(values: tuple[str, ...]) -> str | None:
    parts = [part.strip() for value in values for part in value.split(",")]
    joined = ",".join(part for part in parts if part)
    return joined or None


@click.group(name="colas")
def colas_group():
    """Search and retrieve COLA records."""
    pass


@colas_group.command(name="list")
@click.option("-q", "--query", help="Full-text search query.")
@click.option(
    "--product-type",
    multiple=True,
    type=click.Choice(
        ["malt beverage", "wine", "distilled spirits"], case_sensitive=False
    ),
    help="Filter by TTB product type. Can be used multiple times.",
)
@click.option(
    "--category",
    multiple=True,
    type=click.Choice(["Beer", "Wine", "Liquor"], case_sensitive=False),
    help="Filter by derived top-level category. Can be used multiple times.",
)
@click.option(
    "--derived-subcategory",
    help='Filter by derived category path prefix, e.g. "Beer > Ale".',
)
@click.option("--origin", help="Filter by origin (country/state).")
@click.option(
    "--domestic-or-imported",
    type=click.Choice(["domestic", "imported"], case_sensitive=False),
    help="Filter by domestic/imported origin.",
)
@click.option("--status", help="Filter by application status.")
@click.option("--brand", "brand_name", help="Filter by brand name (partial match).")
@click.option("--permit-number", help="Filter by exact permit number.")
@click.option("--barcode", "barcode_value", help="Filter by exact main barcode value.")
@click.option(
    "--date-from",
    "approval_date_from",
    help="Filter by minimum approval date (YYYY-MM-DD).",
)
@click.option(
    "--date-to",
    "approval_date_to",
    help="Filter by maximum approval date (YYYY-MM-DD).",
)
@click.option("--abv-min", type=float, help="Filter by minimum ABV.")
@click.option("--abv-max", type=float, help="Filter by maximum ABV.")
@click.option(
    "--volume-unit",
    type=click.Choice(
        [
            "beer barrels",
            "fluid ounces",
            "gallons",
            "liters",
            "milliliters",
            "pints",
            "quarts",
        ],
        case_sensitive=False,
    ),
    help="Filter by package volume unit. Required with --volume-min/--volume-max.",
)
@click.option("--volume-min", type=float, help="Filter by minimum package volume.")
@click.option("--volume-max", type=float, help="Filter by maximum package volume.")
@click.option(
    "--container-type",
    multiple=True,
    type=click.Choice(
        [
            "bag",
            "bottle",
            "box",
            "can",
            "carton",
            "cask",
            "jug",
            "keg",
            "pod",
            "pouch",
        ],
        case_sensitive=False,
    ),
    help="Filter by derived container type. Can be used multiple times.",
)
@click.option(
    "--limit", "per_page", default=20, type=int, help="Results per page (max 100)."
)
@click.option(
    "--sort",
    type=click.Choice(["approval_date_desc", "relevance_desc"], case_sensitive=False),
    help="Sort order. Use relevance_desc with --query for score-first results.",
)
@click.option("--page", default=1, type=int, help="Page number.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def list_colas(
    query: str | None,
    product_type: tuple[str, ...],
    category: tuple[str, ...],
    derived_subcategory: str | None,
    origin: str | None,
    domestic_or_imported: str | None,
    status: str | None,
    brand_name: str | None,
    permit_number: str | None,
    barcode_value: str | None,
    approval_date_from: str | None,
    approval_date_to: str | None,
    abv_min: float | None,
    abv_max: float | None,
    volume_unit: str | None,
    volume_min: float | None,
    volume_max: float | None,
    container_type: tuple[str, ...],
    per_page: int,
    sort: str | None,
    page: int,
    as_json: bool,
):
    """List and search COLA records.

    Examples:

    \b
        # Search for bourbon
        cola colas list -q "bourbon"

    \b
        # List wine or beer from California
        cola colas list --product-type wine --product-type "malt beverage"
          --origin california

    \b
        # Find 12 oz canned beer
        cola colas list --category Beer --container-type can
          --volume-unit "fluid ounces" --volume-min 12 --volume-max 12

    \b
        # Search generic text, including applicant/company names
        cola colas list -q "molson coors"
    """
    try:
        with get_client() as client:
            result = client.list_colas(
                query=query,
                product_type=_join_multi(product_type),
                category=_join_multi(category),
                derived_subcategory=derived_subcategory,
                origin=origin,
                domestic_or_imported=domestic_or_imported,
                status=status,
                brand_name=brand_name,
                permit_number=permit_number,
                barcode_value=barcode_value,
                approval_date_from=approval_date_from,
                approval_date_to=approval_date_to,
                abv_min=abv_min,
                abv_max=abv_max,
                volume_unit=volume_unit,
                volume_min=volume_min,
                volume_max=volume_max,
                container_type=_join_multi(container_type),
                sort=sort,
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
@click.option(
    "--limit", "per_page", default=20, type=int, help="Results per page (max 100)."
)
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
