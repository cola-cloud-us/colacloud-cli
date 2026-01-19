"""Usage command for COLA Cloud CLI."""

import json

import click

from colacloud_cli.api import APIError, get_client
from colacloud_cli.commands.utils import console, handle_api_error
from colacloud_cli.formatters import format_usage


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
