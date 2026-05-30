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
