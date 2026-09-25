"""Custom exceptions and error parser for FruitCraft API."""

from typing import Any, Dict, Optional


class FruitCraftError(Exception):
    """Base exception for all FruitCraft API errors."""

    def __init__(
        self,
        message: str,
        endpoint: Optional[str] = None,
        code: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.endpoint = endpoint
        self.code = code
        self.metadata = metadata or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        parts = []
        if self.endpoint:
            parts.append(f"[{self.endpoint}]")
        if self.code is not None:
            parts.append(f"Error Code {self.code}:")
        parts.append(self.message)
        return " ".join(parts)


class AuthenticationError(FruitCraftError):
    """Raised when authentication fails or session is invalid."""
    pass


class PlayerLoadError(FruitCraftError):
    """Raised when player/load endpoint fails."""
    pass


class ServerError(FruitCraftError):
    """Raised when server returns an internal failure or invalid response."""
    pass


class RateLimitError(FruitCraftError):
    """Raised when request frequency is limited by server."""
    pass


class CaptchaRequiredError(FruitCraftError):
    """Raised when server requires CAPTCHA verification."""
    pass


class InvalidRequestError(FruitCraftError):
    """Raised when request payload or parameters are invalid."""
    pass


class NetworkError(FruitCraftError):
    """Raised when HTTP request times out or experiences connection issues."""
    pass


class UnknownAPIError(FruitCraftError):
    """Raised when unmapped error code is returned."""
    pass


def parse_api_error(endpoint: str, code: int, message: str, raw_response: Dict[str, Any]) -> FruitCraftError:
    """
    Map server status/code into typed FruitCraft error exception.
    Ensures safe error representations without credentials.
    """
    clean_meta = {
        "status": raw_response.get("status"),
        "code": code,
        "needs_captcha": raw_response.get("needs_captcha", False),
    }

    # Common FruitCraft game error code mappings
    if code in (101, 102, 103, 104, 105):
        return AuthenticationError(message, endpoint=endpoint, code=code, metadata=clean_meta)
    elif code in (156, 124, 184):
        return RateLimitError(message, endpoint=endpoint, code=code, metadata=clean_meta)
    elif raw_response.get("needs_captcha", False):
        return CaptchaRequiredError(message, endpoint=endpoint, code=code, metadata=clean_meta)
    elif code >= 500:
        return ServerError(message, endpoint=endpoint, code=code, metadata=clean_meta)
    elif code in (400, 401, 403, 404):
        return InvalidRequestError(message, endpoint=endpoint, code=code, metadata=clean_meta)

    return FruitCraftError(message, endpoint=endpoint, code=code, metadata=clean_meta)
