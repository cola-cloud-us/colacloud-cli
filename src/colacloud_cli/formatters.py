"""Rich table formatters for CLI output."""

from datetime import datetime
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Product type colors for visual distinction
PRODUCT_TYPE_COLORS = {
    "malt beverage": "yellow",
    "wine": "magenta",
    "distilled spirits": "cyan",
}

# Status colors
STATUS_COLORS = {
    "approved": "green",
    "pending": "yellow",
    "expired": "red",
    "active": "green",
    "inactive": "dim",
}


def get_product_type_color(product_type: Optional[str]) -> str:
    """Get color for a product type."""
    if not product_type:
        return "white"
    return PRODUCT_TYPE_COLORS.get(product_type.lower(), "white")


def get_status_color(status: Optional[str]) -> str:
    """Get color for a status value."""
    if not status:
        return "white"
    return STATUS_COLORS.get(status.lower(), "white")


def truncate(text: Optional[str], max_length: int = 30) -> str:
    """Truncate text to max length with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_date(date_str: Optional[str]) -> str:
    """Format ISO date string for display."""
    if not date_str:
        return ""
    try:
        # Parse ISO format date
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        return date_str
    except ValueError:
        return date_str


def format_number(num: Optional[int]) -> str:
    """Format number with thousands separators."""
    if num is None:
        return ""
    return f"{num:,}"


def format_percentage(value: Optional[float]) -> str:
    """Format a percentage value."""
    if value is None:
        return ""
    return f"{value:.1f}%"


def format_cola_table(colas: list[dict[str, Any]], console: Console) -> Table:
    """Create a rich table for COLA listing.

    Args:
        colas: List of COLA data dictionaries.
        console: Rich console for output.

    Returns:
        Configured Rich Table.
    """
    table = Table(show_header=True, header_style="bold")

    # Define columns
    table.add_column("TTB ID", style="bright_blue", no_wrap=True)
    table.add_column("Brand", style="bold")
    table.add_column("Product")
    table.add_column("Type")
    table.add_column("ABV")
    table.add_column("Approved", style="dim")

    for cola in colas:
        product_type = cola.get("product_type", "")
        type_color = get_product_type_color(product_type)

        table.add_row(
            cola.get("ttb_id", ""),
            truncate(cola.get("brand_name"), 20),
            truncate(cola.get("product_name"), 25),
            Text(product_type or "", style=type_color),
            format_percentage(cola.get("abv")),
            format_date(cola.get("approval_date")),
        )

    return table


def format_cola_detail(cola: dict[str, Any], console: Console) -> None:
    """Print detailed COLA information.

    Args:
        cola: COLA data dictionary.
        console: Rich console for output.
    """
    product_type = cola.get("product_type", "")
    type_color = get_product_type_color(product_type)

    # Build header
    header = Text()
    header.append(cola.get("brand_name", "Unknown Brand"), style="bold bright_white")
    header.append("\n")
    header.append(cola.get("product_name", ""), style="italic")

    console.print(Panel(header, title=f"[bright_blue]{cola.get('ttb_id', '')}[/]", border_style="blue"))

    # Basic info table
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Field", style="dim")
    info_table.add_column("Value")

    info_table.add_row("Product Type", Text(product_type, style=type_color))
    info_table.add_row("Class", cola.get("class_name", ""))
    info_table.add_row("Origin", cola.get("origin_name", ""))
    info_table.add_row("Domestic/Imported", cola.get("domestic_or_imported", ""))

    if cola.get("abv"):
        info_table.add_row("ABV", format_percentage(cola.get("abv")))
    if cola.get("volume"):
        volume_str = f"{cola.get('volume')} {cola.get('volume_unit', '')}".strip()
        info_table.add_row("Volume", volume_str)

    console.print()
    console.print("[bold]Basic Information[/]")
    console.print(info_table)

    # Dates
    dates_table = Table(show_header=False, box=None, padding=(0, 2))
    dates_table.add_column("Field", style="dim")
    dates_table.add_column("Value")

    dates_table.add_row("Application Date", format_date(cola.get("application_date")))
    dates_table.add_row("Approval Date", format_date(cola.get("approval_date")))
    if cola.get("expiration_date"):
        dates_table.add_row("Expiration Date", format_date(cola.get("expiration_date")))
    dates_table.add_row("Status", Text(cola.get("application_status", ""), style=get_status_color(cola.get("application_status"))))

    console.print()
    console.print("[bold]Dates & Status[/]")
    console.print(dates_table)

    # Permit info
    console.print()
    console.print("[bold]Permit Information[/]")
    permit_table = Table(show_header=False, box=None, padding=(0, 2))
    permit_table.add_column("Field", style="dim")
    permit_table.add_column("Value")
    permit_table.add_row("Permit Number", cola.get("permit_number", ""))
    permit_table.add_row("Application Type", cola.get("application_type", ""))
    console.print(permit_table)

    # LLM enrichment (if available)
    llm_fields = [
        ("llm_category", "Category"),
        ("llm_category_path", "Category Path"),
        ("llm_product_description", "Description"),
        ("llm_container_type", "Container Type"),
        ("llm_tasting_note_flavors", "Tasting Notes"),
    ]

    has_llm_data = any(cola.get(field) for field, _ in llm_fields)
    if has_llm_data:
        console.print()
        console.print("[bold]Enriched Data[/]")
        llm_table = Table(show_header=False, box=None, padding=(0, 2))
        llm_table.add_column("Field", style="dim")
        llm_table.add_column("Value")

        for field, label in llm_fields:
            value = cola.get(field)
            if value:
                llm_table.add_row(label, str(value))

        console.print(llm_table)

    # Wine-specific fields
    if product_type.lower() == "wine":
        wine_fields = [
            ("grape_varietals", "Grape Varietals"),
            ("wine_vintage_year", "Vintage Year"),
            ("wine_appellation", "Appellation"),
            ("llm_wine_designation", "Designation"),
        ]

        has_wine_data = any(cola.get(field) for field, _ in wine_fields)
        if has_wine_data:
            console.print()
            console.print("[bold]Wine Details[/]")
            wine_table = Table(show_header=False, box=None, padding=(0, 2))
            wine_table.add_column("Field", style="dim")
            wine_table.add_column("Value")

            for field, label in wine_fields:
                value = cola.get(field)
                if value:
                    wine_table.add_row(label, str(value))

            console.print(wine_table)

    # Spirits-specific fields
    if product_type.lower() == "distilled spirits":
        spirits_fields = [
            ("llm_liquor_aged_years", "Aged Years"),
            ("llm_liquor_finishing_process", "Finishing Process"),
            ("llm_liquor_grains", "Grains"),
        ]

        has_spirits_data = any(cola.get(field) for field, _ in spirits_fields)
        if has_spirits_data:
            console.print()
            console.print("[bold]Spirits Details[/]")
            spirits_table = Table(show_header=False, box=None, padding=(0, 2))
            spirits_table.add_column("Field", style="dim")
            spirits_table.add_column("Value")

            for field, label in spirits_fields:
                value = cola.get(field)
                if value:
                    spirits_table.add_row(label, str(value))

            console.print(spirits_table)

    # Beer-specific fields
    if product_type.lower() == "malt beverage":
        beer_fields = [
            ("llm_beer_ibu", "IBU"),
            ("llm_beer_hops_varieties", "Hops Varieties"),
        ]

        has_beer_data = any(cola.get(field) for field, _ in beer_fields)
        if has_beer_data:
            console.print()
            console.print("[bold]Beer Details[/]")
            beer_table = Table(show_header=False, box=None, padding=(0, 2))
            beer_table.add_column("Field", style="dim")
            beer_table.add_column("Value")

            for field, label in beer_fields:
                value = cola.get(field)
                if value:
                    beer_table.add_row(label, str(value))

            console.print(beer_table)

    # Barcode info
    if cola.get("barcode_value"):
        console.print()
        console.print("[bold]Barcode[/]")
        barcode_table = Table(show_header=False, box=None, padding=(0, 2))
        barcode_table.add_column("Field", style="dim")
        barcode_table.add_column("Value")
        barcode_table.add_row("Type", cola.get("barcode_type", ""))
        barcode_table.add_row("Value", cola.get("barcode_value", ""))
        console.print(barcode_table)

    # Images
    images = cola.get("images", [])
    if images:
        console.print()
        console.print(f"[bold]Images ({len(images)})[/]")
        for img in images:
            position = img.get("container_position", "unknown")
            dims = ""
            if img.get("width_pixels") and img.get("height_pixels"):
                dims = f" ({img['width_pixels']}x{img['height_pixels']})"
            console.print(f"  - {position}{dims}")
            if img.get("image_url"):
                console.print(f"    [dim]{img['image_url']}[/]")


def format_permittee_table(permittees: list[dict[str, Any]], console: Console) -> Table:
    """Create a rich table for permittee listing.

    Args:
        permittees: List of permittee data dictionaries.
        console: Rich console for output.

    Returns:
        Configured Rich Table.
    """
    table = Table(show_header=True, header_style="bold")

    table.add_column("Permit #", style="bright_blue", no_wrap=True)
    table.add_column("Company", style="bold")
    table.add_column("State")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("COLAs", justify="right")

    for permittee in permittees:
        is_active = permittee.get("is_active", False)
        status_style = "green" if is_active else "dim"
        status_text = "Active" if is_active else "Inactive"

        table.add_row(
            permittee.get("permit_number", ""),
            truncate(permittee.get("company_name"), 30),
            permittee.get("company_state", ""),
            truncate(permittee.get("permittee_type"), 15),
            Text(status_text, style=status_style),
            format_number(permittee.get("colas")),
        )

    return table


def format_permittee_detail(permittee: dict[str, Any], console: Console) -> None:
    """Print detailed permittee information.

    Args:
        permittee: Permittee data dictionary.
        console: Rich console for output.
    """
    is_active = permittee.get("is_active", False)
    status_style = "green" if is_active else "red"
    status_text = "Active" if is_active else "Inactive"

    # Header
    header = Text()
    header.append(permittee.get("company_name", "Unknown Company"), style="bold bright_white")

    console.print(Panel(header, title=f"[bright_blue]{permittee.get('permit_number', '')}[/]", border_style="blue"))

    # Basic info
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Field", style="dim")
    info_table.add_column("Value")

    info_table.add_row("Status", Text(status_text, style=status_style))
    if permittee.get("active_reason"):
        info_table.add_row("Reason", permittee.get("active_reason", ""))
    info_table.add_row("Type", permittee.get("permittee_type", ""))
    info_table.add_row("State", permittee.get("company_state", ""))
    info_table.add_row("ZIP Code", permittee.get("company_zip_code", ""))

    console.print()
    console.print("[bold]Company Information[/]")
    console.print(info_table)

    # COLA stats
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column("Field", style="dim")
    stats_table.add_column("Value")

    stats_table.add_row("Total COLAs", format_number(permittee.get("colas")))
    stats_table.add_row("Approved COLAs", format_number(permittee.get("colas_approved")))
    if permittee.get("last_cola_application_date"):
        stats_table.add_row("Last Application", format_date(permittee.get("last_cola_application_date")))

    console.print()
    console.print("[bold]COLA Statistics[/]")
    console.print(stats_table)

    # Recent COLAs
    recent_colas = permittee.get("recent_colas", [])
    if recent_colas:
        console.print()
        console.print(f"[bold]Recent COLAs ({len(recent_colas)})[/]")
        colas_table = format_cola_table(recent_colas, console)
        console.print(colas_table)


def format_barcode_result(data: dict[str, Any], console: Console) -> None:
    """Print barcode lookup result.

    Args:
        data: Barcode lookup data dictionary.
        console: Rich console for output.
    """
    # Header
    header = Text()
    header.append(data.get("barcode_value", ""), style="bold bright_white")
    if data.get("barcode_type"):
        header.append(f"  ({data['barcode_type']})", style="dim")

    console.print(Panel(header, title="Barcode Lookup", border_style="blue"))

    console.print(f"\n[bold]{data.get('total_colas', 0)} COLA(s) found[/]\n")

    colas = data.get("colas", [])
    if colas:
        table = format_cola_table(colas, console)
        console.print(table)


def format_usage(data: dict[str, Any], console: Console) -> None:
    """Print API usage statistics.

    Args:
        data: Usage data dictionary.
        console: Rich console for output.
    """
    console.print(Panel("[bold]API Usage Statistics[/]", border_style="blue"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim")
    table.add_column("Value")

    table.add_row("Tier", Text(data.get("tier", "unknown"), style="bold cyan"))
    table.add_row("Current Period", data.get("current_period", ""))

    # Usage bar
    used = data.get("requests_used", 0)
    limit = data.get("monthly_limit", 1)
    remaining = data.get("requests_remaining", 0)
    usage_pct = (used / limit * 100) if limit > 0 else 0

    # Color based on usage
    if usage_pct >= 90:
        usage_color = "red"
    elif usage_pct >= 75:
        usage_color = "yellow"
    else:
        usage_color = "green"

    table.add_row(
        "Monthly Usage",
        Text(f"{format_number(used)} / {format_number(limit)} ({usage_pct:.1f}%)", style=usage_color),
    )
    table.add_row("Remaining", format_number(remaining))
    table.add_row("Rate Limit", f"{data.get('per_minute_limit', 0)} requests/minute")

    console.print(table)


def format_pagination(pagination: dict[str, Any], console: Console) -> None:
    """Print pagination information.

    Args:
        pagination: Pagination data dictionary.
        console: Rich console for output.
    """
    page = pagination.get("page", 1)
    pages = pagination.get("pages", 1)
    total = pagination.get("total", 0)
    per_page = pagination.get("per_page", 20)

    # Calculate showing range
    start = (page - 1) * per_page + 1
    end = min(page * per_page, total)

    if total > 0:
        console.print(f"\n[dim]Showing {start}-{end} of {format_number(total)} results (page {page} of {pages})[/]")
    else:
        console.print("\n[dim]No results found[/]")


def format_config(config: dict[str, Any], console: Console) -> None:
    """Print configuration information.

    Args:
        config: Configuration dictionary.
        console: Rich console for output.
    """
    console.print(Panel("[bold]COLA Cloud CLI Configuration[/]", border_style="blue"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Setting", style="dim")
    table.add_column("Value")

    # API Key
    api_key = config.get("api_key")
    if api_key:
        table.add_row("API Key", api_key)
    else:
        table.add_row("API Key", Text("Not configured", style="yellow"))

    table.add_row("API Key Source", config.get("api_key_source", "unknown"))
    table.add_row("Config File", config.get("config_file", ""))

    if config.get("api_base_url"):
        table.add_row("API Base URL", config.get("api_base_url"))

    console.print(table)
