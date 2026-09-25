"""API package for FruitCraft client."""

from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.api.crypto import decrypt_response, encrypt_payload, xor_bytes
from fruitcraft_bot.api.errors import (
    AuthenticationError,
    CaptchaRequiredError,
    FruitCraftError,
    InvalidRequestError,
    NetworkError,
    PlayerLoadError,
    RateLimitError,
    ServerError,
    UnknownAPIError,
)
from fruitcraft_bot.api.models import APIResponse, PlayerLoadRequest

__all__ = [
    "FruitCraftAPIClient",
    "encrypt_payload",
    "decrypt_response",
    "xor_bytes",
    "FruitCraftError",
    "AuthenticationError",
    "PlayerLoadError",
    "ServerError",
    "RateLimitError",
    "CaptchaRequiredError",
    "InvalidRequestError",
    "NetworkError",
    "UnknownAPIError",
    "APIResponse",
    "PlayerLoadRequest",
]
