"""Asynchronous HTTP Client for FruitCraft API."""

import asyncio
import logging
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, Union

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from fruitcraft_bot.api.crypto import DEFAULT_XOR_KEY, decrypt_response, encrypt_payload
from fruitcraft_bot.api.errors import (
    AuthenticationError,
    CaptchaRequiredError,
    FruitCraftError,
    NetworkError,
    RateLimitError,
    parse_api_error,
)
from fruitcraft_bot.api.models import APIResponse

logger = logging.getLogger("fruitcraft.api.client")

# Special retry delays in seconds for FruitCraft rate-limit error codes
RETRY_DELAYS_BY_CODE = {
    156: 4.0,
    124: 2.0,
    184: 2.0,
}


class FruitCraftAPIClient:
    """Async API Client for FruitCraft endpoints."""

    def __init__(
        self,
        passport: Optional[str] = None,
        base_url: str = "http://iran.fruitcraft.ir",
        xor_key: str = DEFAULT_XOR_KEY,
        user_agent: str = "Dalvik/2.1.0 (Linux; U; Android 7.1.2; google pixel 2 Build/N2G47H)",
        timeout: float = 15.0,
        max_retries: int = 3,
    ):
        self._passport = passport
        self.base_url = base_url.rstrip("/")
        self.xor_key = xor_key
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_retries = max_retries
        self._http_client: Any = None

    @property
    def passport(self) -> Optional[str]:
        return self._passport

    @passport.setter
    def passport(self, value: Optional[str]):
        self._passport = value

    async def _get_client(self) -> Any:
        if HAS_HTTPX:
            if self._http_client is None or self._http_client.is_closed:
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "User-Agent": self.user_agent,
                    "Host": self.base_url.replace("http://", "").replace("https://", "").split("/")[0],
                }
                self._http_client = httpx.AsyncClient(
                    headers=headers,
                    timeout=httpx.Timeout(self.timeout),
                    follow_redirects=True,
                    trust_env=False,
                )
            return self._http_client
        return None

    async def close(self):
        """Close underlying HTTP client."""
        if HAS_HTTPX and self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def _post_urllib_fallback(self, url: str, content_str: str, headers: Dict[str, str]):
        def _do_post():
            proxy_handler = urllib.request.ProxyHandler({})
            opener = urllib.request.build_opener(proxy_handler)
            req = urllib.request.Request(
                url,
                data=content_str.encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with opener.open(req, timeout=self.timeout) as resp:
                    resp_body = resp.read()
                    resp_headers = dict(resp.headers)
                    return resp.status, resp_body, resp_headers
            except urllib.error.HTTPError as e:
                resp_body = e.read()
                resp_headers = dict(e.headers)
                return e.code, resp_body, resp_headers
            except Exception as e:
                raise NetworkError(f"HTTP Connection failed: {e}", endpoint=url)

        return await asyncio.to_thread(_do_post)

    async def request(
        self,
        endpoint: str,
        payload: Union[Any, Dict[str, Any]],
        passport: Optional[str] = None,
    ) -> APIResponse:
        """
        Send an encrypted POST request to FruitCraft endpoint.
        Handles retries, rate limits, decryption, and error wrapping.
        """
        target_passport = passport or self._passport
        clean_endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/{clean_endpoint}"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": self.user_agent,
            "Host": self.base_url.replace("http://", "").replace("https://", "").split("/")[0],
        }
        if target_passport:
            headers["Cookie"] = f"FRUITPASSPORT={target_passport}"

        encrypted_body = encrypt_payload(payload, self.xor_key)

        retries = 0
        backoff = 1.0

        while True:
            start_time = time.monotonic()
            logger.debug("POST %s (attempt %d/%d)", clean_endpoint, retries + 1, self.max_retries + 1)

            try:
                if HAS_HTTPX:
                    client = await self._get_client()
                    response = await client.post(
                        url,
                        content=encrypted_body,
                        headers=headers,
                    )
                    status_code = response.status_code
                    response_content = response.content
                    response_cookies = response.cookies
                else:
                    status_code, response_content, resp_hdrs = await self._post_urllib_fallback(url, encrypted_body, headers)
                    response_cookies = {}
                    if "Set-Cookie" in resp_hdrs and "FRUITPASSPORT=" in resp_hdrs["Set-Cookie"]:
                        cookie_part = resp_hdrs["Set-Cookie"].split("FRUITPASSPORT=")[1].split(";")[0]
                        response_cookies["FRUITPASSPORT"] = cookie_part

                duration = time.monotonic() - start_time
                logger.debug("HTTP %s %s [%.2fs]", status_code, clean_endpoint, duration)

                if status_code >= 500:
                    if retries < self.max_retries:
                        retries += 1
                        await asyncio.sleep(backoff)
                        backoff *= 2.0
                        continue
                    raise FruitCraftError(f"HTTP Server Error {status_code}", endpoint=clean_endpoint)

                # Decrypt body
                decrypted_json = decrypt_response(response_content, self.xor_key)

                # Update passport if set in cookies
                if "FRUITPASSPORT" in response_cookies:
                    self._passport = response_cookies["FRUITPASSPORT"]

                # Handle raw non-dict response gracefully
                if not isinstance(decrypted_json, dict):
                    return APIResponse(status=True, data=decrypted_json)

                # Extract status and codes
                status = decrypted_json.get("status", True)
                if isinstance(status, str):
                    status = status.lower() in ("true", "1", "ok")

                code = decrypted_json.get("code", 0)
                data = decrypted_json.get("data", decrypted_json)
                needs_captcha = decrypted_json.get("needs_captcha", False)
                server_msg = (
                    decrypted_json.get("message")
                    or decrypted_json.get("error")
                    or decrypted_json.get("msg")
                    or decrypted_json.get("text")
                    or (str(decrypted_json.get("data")) if isinstance(decrypted_json.get("data"), str) else "")
                    or f"Server returned status false (code: {code})"
                )

                # Handle FruitCraft specific retry error codes
                if code in RETRY_DELAYS_BY_CODE and retries < self.max_retries:
                    retry_delay = RETRY_DELAYS_BY_CODE[code]
                    logger.warning("Rate limit hit code=%d on %s. Retrying after %.1fs...", code, clean_endpoint, retry_delay)
                    retries += 1
                    await asyncio.sleep(retry_delay)
                    continue

                if not status or (isinstance(code, int) and code != 0):
                    logger.debug("Full server response for %s: %s", clean_endpoint, decrypted_json)
                    err = parse_api_error(clean_endpoint, int(code or 0), str(server_msg), decrypted_json)
                    logger.error("%s failed: %s", clean_endpoint, err)
                    raise err

                if needs_captcha:
                    logger.warning("CAPTCHA required on %s", clean_endpoint)

                return APIResponse(
                    status=True,
                    data=data,
                    needs_captcha=needs_captcha,
                    time=decrypted_json.get("time"),
                    code=int(code or 0),
                    message=server_msg or None,
                )

            except Exception as exc:
                if isinstance(exc, (FruitCraftError, CaptchaRequiredError, RateLimitError, AuthenticationError)):
                    raise exc
                if retries < self.max_retries:
                    retries += 1
                    logger.warning("Network error on %s (%s). Retrying (attempt %d)...", clean_endpoint, exc, retries)
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue
                raise NetworkError(f"Network request failed for {clean_endpoint}: {exc}", endpoint=clean_endpoint)
