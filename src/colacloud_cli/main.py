"""Main CLI entry point for COLA Cloud CLI."""

import click
from rich.console import Console

from colacloud_cli import __version__
from colacloud_cli.commands.barcode import barcode_command
from colacloud_cli.commands.colas import colas_group
from colacloud_cli.commands.config import config_group
from colacloud_cli.commands.permittees import permittees_group
from colacloud_cli.commands.usage import usage_command

console = Console()


class AliasedGroup(click.Group):
    """Click group that supports command aliases."""

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        # First try exact match
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        # Support common aliases for command groups
        aliases = {
            "s": "colas",
            "p": "permittees",
            "c": "config",
            "b": "barcode",
            "u": "usage",
        }

        if cmd_name in aliases:
            return click.Group.get_command(self, ctx, aliases[cmd_name])

        # Special case: 'cola search <query>' -> 'cola colas search <query>'
        # This requires forwarding remaining args to the search subcommand
        if cmd_name == "search":
            colas_group = click.Group.get_command(self, ctx, "colas")
            if colas_group:
                return colas_group.get_command(ctx, "search")

        return None


@click.group(cls=AliasedGroup)
@click.version_option(version=__version__, prog_name="cola")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """COLA Cloud CLI - Access the TTB COLA Registry from the command line.

    COLA Cloud provides access to the United States TTB (Alcohol and Tobacco
    Tax and Trade Bureau) Certificate of Label Approval registry, containing
    over 1 million alcohol product label records.

    \b
    Quick start:
        1. Get your API key from https://app.colacloud.us
        2. Run: cola config set-key
        3. Start searching: cola colas search "buffalo trace"

    \b
    Commands:
        config      Manage CLI configuration (API key)
        colas       Search and retrieve COLA records
        permittees  Search and retrieve permittee records
        barcode     Look up products by barcode
        usage       Show your API usage statistics

    \b
    Examples:
        cola colas search "bourbon"
        cola colas list --product-type wine --origin california
        cola permittees list --state KY
        cola barcode 012345678901
        cola usage

    For more information, visit https://colacloud.us/docs/api
    """
    ctx.ensure_object(dict)


# Register command groups
cli.add_command(config_group)
cli.add_command(colas_group)
cli.add_command(permittees_group)
cli.add_command(barcode_command)
cli.add_command(usage_command)


def main() -> None:
    """Entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/]")
        raise SystemExit(130)
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
