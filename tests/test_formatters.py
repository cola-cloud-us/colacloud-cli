from rich.console import Console

from colacloud_cli.formatters import format_pagination


def _render_pagination(pagination: dict) -> str:
    console = Console(record=True, width=100)
    format_pagination(pagination, console)
    return console.export_text()


def test_format_pagination_handles_unknown_total_with_more_results():
    output = _render_pagination(
        {
            "mode": "offset",
            "page": 1,
            "per_page": 3,
            "total": None,
            "pages": None,
            "has_more": True,
        }
    )

    assert "Showing page 1 (more results available)" in output


def test_format_pagination_handles_unknown_total_at_end():
    output = _render_pagination(
        {
            "mode": "offset",
            "page": 2,
            "per_page": 3,
            "total": None,
            "pages": None,
            "has_more": False,
        }
    )

    assert "Showing page 2 (end of results)" in output


def test_trade_name_is_displayed_as_literal_source_text():
    from colacloud_cli.formatters import format_cola_detail

    console = Console(record=True, width=120)
    format_cola_detail(
        {"ttb_id": "123", "applicant_trade_name": "[bold]Wine & Co[/bold]"}, console
    )
    output = console.export_text()
    assert "Trade name used on label" in output
    assert "[bold]Wine & Co[/bold]" in output
