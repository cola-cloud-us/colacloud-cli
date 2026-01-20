"""Tests for API client."""

import os

import httpx
import pytest
import respx

from colacloud_cli.api import (
    APIError,
    AuthenticationError,
    ColaCloudClient,
    RateLimitError,
)
from colacloud_cli.config import API_KEY_ENV_VAR


@pytest.fixture
def api_key():
    """Set up API key for tests."""
    os.environ[API_KEY_ENV_VAR] = "test_api_key_123"
    yield "test_api_key_123"
    del os.environ[API_KEY_ENV_VAR]


@pytest.fixture
def client(api_key):
    """Create a test client."""
    return ColaCloudClient(api_key=api_key, base_url="https://test.colacloud.us/api/v1")


class TestColaCloudClient:
    def test_client_initialization(self, api_key):
        """Client initializes with API key."""
        client = ColaCloudClient(api_key=api_key)
        assert client.api_key == api_key

    def test_client_requires_api_key(self):
        """Client raises error when API key is missing."""
        old_value = os.environ.pop(API_KEY_ENV_VAR, None)
        try:
            client = ColaCloudClient()
            with pytest.raises(AuthenticationError):
                client._require_api_key()
        finally:
            if old_value:
                os.environ[API_KEY_ENV_VAR] = old_value

    def test_client_headers(self, client):
        """Client includes correct headers."""
        headers = client._get_headers()
        assert headers["X-API-Key"] == "test_api_key_123"
        assert "User-Agent" in headers
        assert "colacloud-cli" in headers["User-Agent"]

    def test_context_manager(self, api_key):
        """Client works as context manager."""
        with ColaCloudClient(api_key=api_key) as client:
            assert client.api_key == api_key


class TestListColas:
    @respx.mock
    def test_list_colas_basic(self, client):
        """list_colas returns search results."""
        respx.get("https://test.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [{"ttb_id": "123", "brand_name": "Test Brand"}],
                    "pagination": {"page": 1, "total": 1},
                },
            )
        )

        result = client.list_colas(query="test")
        assert len(result["data"]) == 1
        assert result["data"][0]["brand_name"] == "Test Brand"

    @respx.mock
    def test_list_colas_with_filters(self, client):
        """list_colas passes filter parameters."""
        route = respx.get("https://test.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(200, json={"data": [], "pagination": {}})
        )

        client.list_colas(
            query="bourbon",
            product_type="distilled spirits",
            origin="kentucky",
            abv_min=40.0,
        )

        request = route.calls[0].request
        assert "q=bourbon" in str(request.url)
        assert "product_type=distilled" in str(request.url)
        assert "origin=kentucky" in str(request.url)
        assert "abv_min=40" in str(request.url)


class TestGetCola:
    @respx.mock
    def test_get_cola(self, client):
        """get_cola returns COLA details."""
        respx.get("https://test.colacloud.us/api/v1/colas/12345").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"ttb_id": "12345", "brand_name": "Test"}},
            )
        )

        result = client.get_cola("12345")
        assert result["data"]["ttb_id"] == "12345"

    @respx.mock
    def test_get_cola_not_found(self, client):
        """get_cola raises APIError for 404."""
        respx.get("https://test.colacloud.us/api/v1/colas/99999").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"code": "not_found", "message": "COLA not found"}},
            )
        )

        with pytest.raises(APIError) as exc_info:
            client.get_cola("99999")

        assert exc_info.value.status_code == 404
        assert exc_info.value.error_code == "not_found"


class TestPermittees:
    @respx.mock
    def test_list_permittees(self, client):
        """list_permittees returns results."""
        respx.get("https://test.colacloud.us/api/v1/permittees").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"permit_number": "KY-1234"}], "pagination": {}},
            )
        )

        result = client.list_permittees(state="KY")
        assert len(result["data"]) == 1

    @respx.mock
    def test_get_permittee(self, client):
        """get_permittee returns details."""
        respx.get("https://test.colacloud.us/api/v1/permittees/KY-1234").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"permit_number": "KY-1234", "company_name": "Test Co"}},
            )
        )

        result = client.get_permittee("KY-1234")
        assert result["data"]["company_name"] == "Test Co"


class TestBarcode:
    @respx.mock
    def test_lookup_barcode(self, client):
        """lookup_barcode returns results."""
        respx.get("https://test.colacloud.us/api/v1/barcode/012345678901").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"barcode": "012345678901", "colas": []}},
            )
        )

        result = client.lookup_barcode("012345678901")
        assert result["data"]["barcode"] == "012345678901"


class TestUsage:
    @respx.mock
    def test_get_usage(self, client):
        """get_usage returns usage stats."""
        respx.get("https://test.colacloud.us/api/v1/usage").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"requests_used": 100, "requests_limit": 500}},
            )
        )

        result = client.get_usage()
        assert result["data"]["requests_used"] == 100


class TestErrorHandling:
    @respx.mock
    def test_authentication_error(self, client):
        """401 raises AuthenticationError."""
        respx.get("https://test.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(
                401,
                json={"error": {"code": "invalid_api_key", "message": "Invalid API key"}},
            )
        )

        with pytest.raises(AuthenticationError) as exc_info:
            client.list_colas()

        assert exc_info.value.status_code == 401

    @respx.mock
    def test_rate_limit_error(self, client):
        """429 raises RateLimitError with retry_after."""
        respx.get("https://test.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(
                429,
                headers={"Retry-After": "60"},
                json={"error": {"code": "rate_limited", "message": "Too many requests"}},
            )
        )

        with pytest.raises(RateLimitError) as exc_info:
            client.list_colas()

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 60

    @respx.mock
    def test_server_error(self, client):
        """500 raises APIError."""
        respx.get("https://test.colacloud.us/api/v1/colas").mock(
            return_value=httpx.Response(
                500,
                json={"error": {"code": "server_error", "message": "Internal error"}},
            )
        )

        with pytest.raises(APIError) as exc_info:
            client.list_colas()

        assert exc_info.value.status_code == 500
