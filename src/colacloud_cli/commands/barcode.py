"""Barcode lookup command for COLA Cloud CLI."""

import json

import click

from colacloud_cli.api import APIError, get_client
from colacloud_cli.commands.utils import console, handle_api_error
from colacloud_cli.formatters import format_barcode_result


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
