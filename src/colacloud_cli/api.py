"""COLA Cloud API client wrapper."""

from typing import Any, Optional

import httpx

from colacloud_cli import __version__
from colacloud_cli.config import get_config


class APIError(Exception):
    """Exception raised for API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.insert(0, f"[{self.status_code}]")
        if self.error_code:
            parts.insert(0, f"({self.error_code})")
        return " ".join(parts)


class AuthenticationError(APIError):
    """Exception raised for authentication errors."""

    pass


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ColaCloudClient:
    """HTTP client for the COLA Cloud API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize the API client.

        Args:
            api_key: API key for authentication. If not provided,
                    will be read from config.
            base_url: API base URL. If not provided, will use default.
            timeout: Request timeout in seconds.
        """
        config = get_config()
        self.api_key = api_key or config.get_api_key()
        self.base_url = (base_url or config.get_api_base_url()).rstrip("/")
        self.timeout = timeout

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._get_headers(),
        )

    def _get_headers(self) -> dict[str, str]:
        """Get request headers including authentication."""
        headers = {
            "Accept": "application/json",
            "User-Agent": f"colacloud-cli/{__version__}",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions.

        Args:
            response: HTTP response object.

        Returns:
            Parsed JSON response data.

        Raises:
            AuthenticationError: If authentication fails.
            RateLimitError: If rate limit is exceeded.
            APIError: For other API errors.
        """
        # Try to parse JSON response
        try:
            data = response.json()
        except (ValueError, httpx.DecodingError):
            data = {}

        # Handle successful responses
        if response.is_success:
            return data

        # Extract error information
        error_info = data.get("error", {})
        error_code = error_info.get("code", "unknown_error")
        error_message = error_info.get("message", response.reason_phrase or "Unknown error")
        error_details = error_info.get("details", {})

        # Handle specific error types
        if response.status_code == 401:
            raise AuthenticationError(
                error_message,
                status_code=response.status_code,
                error_code=error_code,
                details=error_details,
            )

        if response.status_code == 429:
            retry_after = None
            if "Retry-After" in response.headers:
                try:
                    retry_after = int(response.headers["Retry-After"])
                except ValueError:
                    pass

            raise RateLimitError(
                error_message,
                status_code=response.status_code,
                error_code=error_code,
                details=error_details,
                retry_after=retry_after,
            )

        raise APIError(
            error_message,
            status_code=response.status_code,
            error_code=error_code,
            details=error_details,
        )

    def _require_api_key(self) -> None:
        """Ensure API key is configured.

        Raises:
            AuthenticationError: If API key is not configured.
        """
        if not self.api_key:
            raise AuthenticationError(
                "API key not configured. Run 'cola config set-key' to set your API key, "
                "or set the COLACLOUD_API_KEY environment variable."
            )

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "ColaCloudClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # COLA endpoints

    def list_colas(
        self,
        query: Optional[str] = None,
        product_type: Optional[str] = None,
        origin: Optional[str] = None,
        brand_name: Optional[str] = None,
        approval_date_from: Optional[str] = None,
        approval_date_to: Optional[str] = None,
        abv_min: Optional[float] = None,
        abv_max: Optional[float] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """Search and filter COLAs.

        Args:
            query: Full-text search query.
            product_type: Filter by product type (malt beverage, wine, distilled spirits).
            origin: Filter by country/state.
            brand_name: Filter by brand name (partial match).
            approval_date_from: Filter by minimum approval date (YYYY-MM-DD).
            approval_date_to: Filter by maximum approval date (YYYY-MM-DD).
            abv_min: Filter by minimum ABV.
            abv_max: Filter by maximum ABV.
            page: Page number.
            per_page: Results per page (max 100).

        Returns:
            API response with data and pagination info.
        """
        self._require_api_key()

        params = {"page": page, "per_page": per_page}

        if query:
            params["q"] = query
        if product_type:
            params["product_type"] = product_type
        if origin:
            params["origin"] = origin
        if brand_name:
            params["brand_name"] = brand_name
        if approval_date_from:
            params["approval_date_from"] = approval_date_from
        if approval_date_to:
            params["approval_date_to"] = approval_date_to
        if abv_min is not None:
            params["abv_min"] = abv_min
        if abv_max is not None:
            params["abv_max"] = abv_max

        response = self._client.get("/colas", params=params)
        return self._handle_response(response)

    def get_cola(self, ttb_id: str) -> dict[str, Any]:
        """Get a single COLA by TTB ID.

        Args:
            ttb_id: The TTB ID of the COLA.

        Returns:
            API response with COLA details.
        """
        self._require_api_key()

        response = self._client.get(f"/colas/{ttb_id}")
        return self._handle_response(response)

    # Permittee endpoints

    def list_permittees(
        self,
        query: Optional[str] = None,
        state: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """Search permittees.

        Args:
            query: Search by company name (partial match).
            state: Filter by state.
            is_active: Filter by active status.
            page: Page number.
            per_page: Results per page (max 100).

        Returns:
            API response with data and pagination info.
        """
        self._require_api_key()

        params = {"page": page, "per_page": per_page}

        if query:
            params["q"] = query
        if state:
            params["state"] = state.upper()
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"

        response = self._client.get("/permittees", params=params)
        return self._handle_response(response)

    def get_permittee(self, permit_number: str) -> dict[str, Any]:
        """Get a single permittee by permit number.

        Args:
            permit_number: The permit number.

        Returns:
            API response with permittee details.
        """
        self._require_api_key()

        response = self._client.get(f"/permittees/{permit_number}")
        return self._handle_response(response)

    # Barcode endpoint

    def lookup_barcode(self, barcode_value: str) -> dict[str, Any]:
        """Look up COLAs by barcode.

        Args:
            barcode_value: The barcode value (UPC, EAN, etc.).

        Returns:
            API response with barcode info and associated COLAs.
        """
        self._require_api_key()

        response = self._client.get(f"/barcode/{barcode_value}")
        return self._handle_response(response)

    # Usage endpoint

    def get_usage(self) -> dict[str, Any]:
        """Get current API usage statistics.

        Returns:
            API response with usage data.
        """
        self._require_api_key()

        response = self._client.get("/usage")
        return self._handle_response(response)


# Convenience function to get a client instance
def get_client(**kwargs) -> ColaCloudClient:
    """Get a ColaCloudClient instance.

    Args:
        **kwargs: Arguments to pass to ColaCloudClient constructor.

    Returns:
        ColaCloudClient instance.
    """
    return ColaCloudClient(**kwargs)
