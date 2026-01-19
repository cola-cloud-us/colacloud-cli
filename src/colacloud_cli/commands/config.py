"""Configuration commands for COLA Cloud CLI."""

import json

import click
from rich.console import Console

from colacloud_cli.config import get_config
from colacloud_cli.formatters import format_config

console = Console()


@click.group(name="config")
def config_group():
    """Manage CLI configuration."""
    pass


@config_group.command(name="set-key")
@click.option(
    "--key",
    "-k",
    help="API key to set. If not provided, will prompt for input.",
)
def set_key(key: str | None):
    """Set your COLA Cloud API key.

    The API key will be saved to ~/.colacloud/config.json with restricted
    permissions (readable only by you).

    You can also set the COLACLOUD_API_KEY environment variable instead.
    """
    config = get_config()

    if key is None:
        # Prompt for API key with hidden input
        key = click.prompt(
            "Enter your API key",
            hide_input=True,
            confirmation_prompt=True,
        )

    if not key or not key.strip():
        console.print("[red]Error:[/] API key cannot be empty.")
        raise SystemExit(1)

    key = key.strip()
    config.set_api_key(key)

    console.print("[green]Success![/] API key saved to ~/.colacloud/config.json")
    console.print("[dim]The config file has been set to mode 600 (owner read/write only).[/]")


@config_group.command(name="show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def show(as_json: bool):
    """Show current configuration.

    API key will be partially masked for security.
    """
    config = get_config()
    config_data = config.to_dict()

    if as_json:
        click.echo(json.dumps(config_data, indent=2))
    else:
        format_config(config_data, console)


@config_group.command(name="clear")
@click.confirmation_option(prompt="Are you sure you want to clear your configuration?")
def clear():
    """Clear all saved configuration.

    This will remove your saved API key and any other settings.
    """
    config = get_config()
    config.clear()
    console.print("[green]Configuration cleared.[/]")
