# COLA Cloud CLI

This is the public command-line client for the COLA Cloud API. Keep this repo safe for public GitHub: do not add private workspace notes, credentials, customer data, or internal-only infrastructure details.

## Development

- Use `uv sync` to install dependencies.
- Run tests with `uv run pytest`.
- Run linting with `uv run ruff check .`.
- Source code lives in `src/colacloud_cli`; tests live in `tests`.

## API Work

- Unit tests should mock HTTP calls rather than hitting production services.
- Smoke tests may require `COLA_API_KEY`; do not hardcode API keys or tokens.
- Avoid accidental CLI behavior breaks. If a breaking change is intentional, make it explicit in the versioning/release notes.
