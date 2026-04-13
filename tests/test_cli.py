"""Tests for CLI commands."""

import json
import os

import httpx
import pytest
import respx
from click.testing import CliRunner

from colacloud_cli.config import API_KEY_ENV_VAR
from colacloud_cli.main import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def api_key():
    """Set up API key for tests."""
    os.environ[API_KEY_ENV_VAR] = "test_api_key"
    yield
    os.environ.pop(API_KEY_ENV_VAR, None)


class TestCLIBasic:
    def test_help(self, runner):
        """CLI shows help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "COLA Cloud CLI" in result.output

    def test_version(self, runner):
        """CLI shows version."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "cola" in result.output


class TestColasCommands:
    @respx.mock
    def test_colas_list(self, runner, api_key):
        """colas list returns results."""
        respx.get("https://app.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "ttb_id": "12345",
                            "brand_name": "Test Brand",
                            "product_name": "Test Whiskey",
                            "product_type": "distilled spirits",
                            "approval_date": "2024-01-15",
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "total": 1,
                        "per_page": 20,
                        "total_pages": 1,
                    },
                },
            )
        )

        result = runner.invoke(cli, ["colas", "list", "-q", "test"])
        assert result.exit_code == 0
        assert "Test Brand" in result.output

    @respx.mock
    def test_colas_list_json(self, runner, api_key):
        """colas list --json outputs JSON."""
        respx.get("https://app.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"ttb_id": "12345"}], "pagination": {}},
            )
        )

        result = runner.invoke(cli, ["colas", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "data" in data

    @respx.mock
    def test_colas_list_empty(self, runner, api_key):
        """colas list shows message when no results."""
        respx.get("https://app.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(200, json={"data": [], "pagination": {}})
        )

        result = runner.invoke(cli, ["colas", "list", "-q", "nonexistent"])
        assert result.exit_code == 0
        assert "No COLAs found" in result.output

    @respx.mock
    def test_colas_get(self, runner, api_key):
        """colas get returns COLA details."""
        respx.get("https://app.colacloud.us/api/v1/colas/12345").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "ttb_id": "12345",
                        "brand_name": "Test Brand",
                        "product_name": "Test Product",
                        "product_type": "wine",
                        "origin": "California",
                        "approval_date": "2024-01-01",
                    }
                },
            )
        )

        result = runner.invoke(cli, ["colas", "get", "12345"])
        assert result.exit_code == 0
        assert "Test Brand" in result.output

    @respx.mock
    def test_colas_search(self, runner, api_key):
        """colas search is a shortcut for list -q."""
        respx.get("https://app.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"ttb_id": "1", "brand_name": "Bourbon Brand"}],
                    "pagination": {"page": 1, "total": 1},
                },
            )
        )

        result = runner.invoke(cli, ["colas", "search", "bourbon"])
        assert result.exit_code == 0
        assert "Bourbon Brand" in result.output


class TestPermitteesCommands:
    @respx.mock
    def test_permittees_list(self, runner, api_key):
        """permittees list returns results."""
        respx.get("https://app.colacloud.us/api/v1/permittees").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "permit_number": "KY-I-123",
                            "company_name": "Kentucky Distillery",
                            "state": "KY",
                            "is_active": True,
                        }
                    ],
                    "pagination": {"page": 1, "total": 1},
                },
            )
        )

        result = runner.invoke(cli, ["permittees", "list", "--state", "KY"])
        assert result.exit_code == 0
        assert "Kentucky Distillery" in result.output

    @respx.mock
    def test_permittees_get(self, runner, api_key):
        """permittees get returns details."""
        respx.get("https://app.colacloud.us/api/v1/permittees/KY-I-123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "permit_number": "KY-I-123",
                        "company_name": "Kentucky Distillery",
                        "state": "KY",
                    }
                },
            )
        )

        result = runner.invoke(cli, ["permittees", "get", "KY-I-123"])
        assert result.exit_code == 0
        assert "Kentucky Distillery" in result.output


class TestBarcodeCommand:
    @respx.mock
    def test_barcode_lookup(self, runner, api_key):
        """barcode command looks up barcodes."""
        respx.get("https://app.colacloud.us/api/v1/barcode/012345678901").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "barcode": "012345678901",
                        "barcode_type": "UPC-A",
                        "colas": [{"ttb_id": "123", "brand_name": "Test"}],
                    }
                },
            )
        )

        result = runner.invoke(cli, ["barcode", "012345678901"])
        assert result.exit_code == 0
        assert "UPC-A" in result.output


class TestUsageCommand:
    @respx.mock
    def test_usage(self, runner, api_key):
        """usage command shows API usage."""
        respx.get("https://app.colacloud.us/api/v1/usage").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "tier": "free",
                        "current_period": "2024-01",
                        "detail_views": {"used": 50, "limit": 200, "remaining": 150},
                        "list_records": {"used": 1000, "limit": 10000, "remaining": 9000},
                        "per_minute_limit": 10,
                    }
                },
            )
        )

        result = runner.invoke(cli, ["usage"])
        assert result.exit_code == 0
        assert "50" in result.output


class TestConfigCommands:
    def test_config_show(self, runner):
        """config show displays configuration."""
        result = runner.invoke(cli, ["config", "show"])
        assert result.exit_code == 0
        assert "config" in result.output.lower() or "api" in result.output.lower()


class TestProcessingTimesCommands:
    @respx.mock
    def test_processing_times_list(self, runner, api_key):
        """processing-times list returns results."""
        respx.get("https://app.colacloud.us/api/v1/processing-times").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"commodity": "wine", "avg_days": 30}],
                    "meta": {"total": 1},
                },
            )
        )

        result = runner.invoke(cli, ["processing-times", "list"])
        assert result.exit_code == 0
        assert "wine" in result.output

    @respx.mock
    def test_processing_times_list_json(self, runner, api_key):
        """processing-times list --json outputs JSON."""
        respx.get("https://app.colacloud.us/api/v1/processing-times").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"commodity": "wine"}],
                    "meta": {"total": 1},
                },
            )
        )

        result = runner.invoke(cli, ["processing-times", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "data" in data

    @respx.mock
    def test_processing_times_list_empty(self, runner, api_key):
        """processing-times list shows message when no results."""
        respx.get("https://app.colacloud.us/api/v1/processing-times").mock(
            return_value=httpx.Response(
                200, json={"data": [], "meta": {"total": 0}}
            )
        )

        result = runner.invoke(cli, ["processing-times", "list"])
        assert result.exit_code == 0
        assert "No processing times found" in result.output

    @respx.mock
    def test_processing_times_formula(self, runner, api_key):
        """processing-times formula returns results."""
        respx.get(
            "https://app.colacloud.us/api/v1/processing-times/formula"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"formula_type": "domestic", "avg_days": 20}],
                    "meta": {"total": 1},
                },
            )
        )

        result = runner.invoke(cli, ["processing-times", "formula"])
        assert result.exit_code == 0
        assert "domestic" in result.output

    @respx.mock
    def test_processing_times_registration(self, runner, api_key):
        """processing-times registration returns results."""
        respx.get(
            "https://app.colacloud.us/api/v1/processing-times/registration"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"category": "beverage", "avg_days": 15}],
                    "meta": {"total": 1},
                },
            )
        )

        result = runner.invoke(cli, ["processing-times", "registration"])
        assert result.exit_code == 0
        assert "beverage" in result.output


class TestProductionReportsCommands:
    @respx.mock
    def test_production_reports_list(self, runner, api_key):
        """production-reports list returns results."""
        respx.get("https://app.colacloud.us/api/v1/production-reports").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"commodity": "wine", "year": 2024, "month": 6}],
                    "meta": {
                        "total": 1,
                        "page": 1,
                        "per_page": 100,
                        "has_more": False,
                    },
                },
            )
        )

        result = runner.invoke(cli, ["production-reports", "list"])
        assert result.exit_code == 0
        assert "wine" in result.output

    @respx.mock
    def test_production_reports_list_json(self, runner, api_key):
        """production-reports list --json outputs JSON."""
        respx.get("https://app.colacloud.us/api/v1/production-reports").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"commodity": "wine"}],
                    "meta": {
                        "total": 1,
                        "page": 1,
                        "per_page": 100,
                        "has_more": False,
                    },
                },
            )
        )

        result = runner.invoke(cli, ["production-reports", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "data" in data

    @respx.mock
    def test_production_reports_list_empty(self, runner, api_key):
        """production-reports list shows message when no results."""
        respx.get("https://app.colacloud.us/api/v1/production-reports").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [],
                    "meta": {
                        "total": 0,
                        "page": 1,
                        "per_page": 100,
                        "has_more": False,
                    },
                },
            )
        )

        result = runner.invoke(cli, ["production-reports", "list"])
        assert result.exit_code == 0
        assert "No production reports found" in result.output

    @respx.mock
    def test_production_reports_list_with_pagination(self, runner, api_key):
        """production-reports list shows pagination hint when has_more."""
        respx.get("https://app.colacloud.us/api/v1/production-reports").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"commodity": "wine"}],
                    "meta": {
                        "total": 200,
                        "page": 1,
                        "per_page": 100,
                        "has_more": True,
                    },
                },
            )
        )

        result = runner.invoke(cli, ["production-reports", "list"])
        assert result.exit_code == 0
        assert "More results available" in result.output


class TestAVAsCommands:
    @respx.mock
    def test_avas_list(self, runner, api_key):
        """avas list returns results."""
        respx.get("https://app.colacloud.us/api/v1/avas").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"id": "napa-valley", "name": "Napa Valley"}],
                    "meta": {"total": 1},
                },
            )
        )

        result = runner.invoke(cli, ["avas", "list"])
        assert result.exit_code == 0
        assert "Napa Valley" in result.output

    @respx.mock
    def test_avas_list_json(self, runner, api_key):
        """avas list --json outputs JSON."""
        respx.get("https://app.colacloud.us/api/v1/avas").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"id": "napa-valley", "name": "Napa Valley"}],
                    "meta": {"total": 1},
                },
            )
        )

        result = runner.invoke(cli, ["avas", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "data" in data

    @respx.mock
    def test_avas_list_empty(self, runner, api_key):
        """avas list shows message when no results."""
        respx.get("https://app.colacloud.us/api/v1/avas").mock(
            return_value=httpx.Response(
                200, json={"data": [], "meta": {"total": 0}}
            )
        )

        result = runner.invoke(cli, ["avas", "list"])
        assert result.exit_code == 0
        assert "No AVAs found" in result.output

    @respx.mock
    def test_avas_get(self, runner, api_key):
        """avas get returns AVA details."""
        respx.get("https://app.colacloud.us/api/v1/avas/napa-valley").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "id": "napa-valley",
                        "name": "Napa Valley",
                        "state": "CA",
                    }
                },
            )
        )

        result = runner.invoke(cli, ["avas", "get", "napa-valley"])
        assert result.exit_code == 0
        assert "Napa Valley" in result.output

    @respx.mock
    def test_avas_get_json(self, runner, api_key):
        """avas get --json outputs JSON."""
        respx.get("https://app.colacloud.us/api/v1/avas/napa-valley").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "id": "napa-valley",
                        "name": "Napa Valley",
                    }
                },
            )
        )

        result = runner.invoke(cli, ["avas", "get", "napa-valley", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "data" in data


class TestCommandAliases:
    @respx.mock
    def test_shortcut_s_for_colas(self, runner, api_key):
        """'s' is an alias for 'colas'."""
        respx.get("https://app.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(200, json={"data": [], "pagination": {}})
        )

        result = runner.invoke(cli, ["s", "list"])
        assert result.exit_code == 0

    @respx.mock
    def test_shortcut_search(self, runner, api_key):
        """'search' at top level works."""
        respx.get("https://app.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(200, json={"data": [], "pagination": {}})
        )

        result = runner.invoke(cli, ["search", "bourbon"])
        assert result.exit_code == 0


class TestErrorHandling:
    @respx.mock
    def test_authentication_error_message(self, runner, api_key):
        """Authentication errors show helpful message."""
        respx.get("https://app.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(
                401,
                json={
                    "error": {"code": "invalid_api_key", "message": "Invalid API key"}
                },
            )
        )

        result = runner.invoke(cli, ["colas", "list"])
        assert result.exit_code == 1  # Error exits with code 1
        assert (
            "Invalid" in result.output
            or "API key" in result.output
            or "Error" in result.output
        )

    @respx.mock
    def test_rate_limit_error_message(self, runner, api_key):
        """Rate limit errors show retry information."""
        respx.get("https://app.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(
                429,
                headers={"Retry-After": "60"},
                json={
                    "error": {"code": "rate_limited", "message": "Rate limit exceeded"}
                },
            )
        )

        result = runner.invoke(cli, ["colas", "list"])
        assert result.exit_code == 1  # Error exits with code 1
        assert (
            "limit" in result.output.lower()
            or "rate" in result.output.lower()
            or "error" in result.output.lower()
        )
