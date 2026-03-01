#!/usr/bin/env python3
"""
Live smoke test for the colacloud-cli.

Runs actual CLI commands against the production API to verify
end-to-end functionality: config handling, HTTP requests, response
formatting, and JSON output parsing.

Usage:
    COLA_API_KEY=... uv run python scripts/smoke_test.py
    COLA_API_KEY=... uv run python scripts/smoke_test.py --base-url http://localhost:5001/api/v1
"""

import argparse
import json
import os
import subprocess
import sys
import time

results: list[tuple[bool, str]] = []


def run_cola(*args: str, env_override: dict | None = None) -> tuple[int, str, str]:
    """Run a cola CLI command and return (exit_code, stdout, stderr)."""
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    proc = subprocess.run(
        ["uv", "run", "cola", *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def check(name: str, fn):
    """Run a single check. Calls fn(), expects it to return or raise."""
    start = time.monotonic()
    try:
        detail = fn()
        elapsed = time.monotonic() - start
        msg = f"  OK  {name} ({elapsed:.2f}s)"
        if detail:
            msg += f" — {detail}"
        results.append((True, msg))
        print(msg)
    except Exception as e:
        elapsed = time.monotonic() - start
        msg = f"FAIL  {name} — {type(e).__name__}: {e} ({elapsed:.2f}s)"
        results.append((False, msg))
        print(msg)


def main():
    parser = argparse.ArgumentParser(description="COLA Cloud CLI smoke test")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override API base URL (default: production)",
    )
    args = parser.parse_args()

    api_key = os.environ.get("COLA_API_KEY") or os.environ.get("COLACLOUD_API_KEY")
    if not api_key:
        print("Error: COLA_API_KEY or COLACLOUD_API_KEY environment variable is required")
        sys.exit(1)

    env = {"COLACLOUD_API_KEY": api_key}
    if args.base_url:
        env["COLACLOUD_BASE_URL"] = args.base_url

    display = args.base_url or "https://app.colacloud.us/api/v1"
    print(f"Smoke testing colacloud CLI against {display}\n")

    # --- --version ---
    def test_version():
        rc, out, _ = run_cola("--version", env_override=env)
        assert rc == 0, f"exit code {rc}"
        assert "cola" in out.lower(), f"unexpected output: {out}"
        return out.strip()

    check("cola --version", test_version)

    # --- colas list --json ---
    ttb_id = None

    def test_colas_list():
        nonlocal ttb_id
        rc, out, err = run_cola("colas", "list", "--limit", "1", "--json", env_override=env)
        assert rc == 0, f"exit code {rc}: {err}"
        data = json.loads(out)
        assert "data" in data, "missing 'data' key"
        assert len(data["data"]) > 0, "no COLAs returned"
        assert "pagination" in data, "missing 'pagination' key"
        cola = data["data"][0]
        ttb_id = cola["ttb_id"]
        return f"total={data['pagination']['total']}, first={ttb_id}"

    check("cola colas list --limit 1 --json", test_colas_list)

    # --- colas get --json ---
    def test_colas_get():
        if not ttb_id:
            return "skipped — no ttb_id from list"
        rc, out, err = run_cola("colas", "get", ttb_id, "--json", env_override=env)
        assert rc == 0, f"exit code {rc}: {err}"
        data = json.loads(out)
        assert "data" in data, "missing 'data' key"
        assert data["data"]["ttb_id"] == ttb_id
        return f"ttb_id={ttb_id}, type={data['data'].get('product_type')}"

    check(f"cola colas get {ttb_id} --json", test_colas_get)

    # --- colas search --json ---
    def test_colas_search():
        rc, out, err = run_cola(
            "colas", "search", "bourbon", "--limit", "5", "--json", env_override=env
        )
        assert rc == 0, f"exit code {rc}: {err}"
        data = json.loads(out)
        assert "data" in data
        return f"found {len(data['data'])} results"

    check('cola colas search "bourbon" --json', test_colas_search)

    # --- permittees list --json ---
    permit_number = None

    def test_permittees_list():
        nonlocal permit_number
        rc, out, err = run_cola(
            "permittees", "list", "--limit", "1", "--json", env_override=env
        )
        assert rc == 0, f"exit code {rc}: {err}"
        data = json.loads(out)
        assert "data" in data
        assert len(data["data"]) > 0
        permit_number = data["data"][0]["permit_number"]
        return f"total={data['pagination']['total']}, first={permit_number}"

    check("cola permittees list --limit 1 --json", test_permittees_list)

    # --- permittees get --json ---
    def test_permittees_get():
        if not permit_number:
            return "skipped — no permit_number from list"
        rc, out, err = run_cola(
            "permittees", "get", permit_number, "--json", env_override=env
        )
        assert rc == 0, f"exit code {rc}: {err}"
        data = json.loads(out)
        assert "data" in data
        return f"permit={permit_number}, company={data['data'].get('company_name')}"

    check(f"cola permittees get {permit_number} --json", test_permittees_get)

    # --- usage --json ---
    def test_usage():
        rc, out, err = run_cola("usage", "--json", env_override=env)
        assert rc == 0, f"exit code {rc}: {err}"
        data = json.loads(out)
        assert "data" in data
        usage = data["data"]
        return f"tier={usage.get('tier')}, used={usage.get('requests_used')}/{usage.get('monthly_limit')}"

    check("cola usage --json", test_usage)

    # --- colas list (table output, no --json) ---
    def test_table_output():
        rc, out, err = run_cola("colas", "list", "--limit", "3", env_override=env)
        assert rc == 0, f"exit code {rc}: {err}"
        assert len(out.strip()) > 0, "empty output"
        return f"{len(out.splitlines())} lines of output"

    check("cola colas list --limit 3 (table)", test_table_output)

    # --- Summary ---
    total = len(results)
    passed = sum(1 for p, _ in results if p)
    failed = total - passed

    print(f"\n{'=' * 40}")
    print(f"  {passed}/{total} passed", end="")
    if failed:
        print(f", {failed} failed")
    else:
        print()

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
