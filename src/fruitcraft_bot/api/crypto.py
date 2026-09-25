"""Crypto routines for FruitCraft API (XOR, Base64, URL encoding)."""

import base64
import json
import urllib.parse
from typing import Any, Dict, Union
from fruitcraft_bot.api.models import BaseModel


DEFAULT_XOR_KEY = "ali1343faraz1055antler288based"


def xor_bytes(data: bytes, key: str) -> bytes:
    """XOR bytes with repeating ASCII key."""
    if not key:
        return data
    key_bytes = key.encode("utf-8")
    key_len = len(key_bytes)
    return bytes(b ^ key_bytes[i % key_len] for i, b in enumerate(data))


def encrypt_payload(payload: Union[BaseModel, Dict[str, Any]], key: str = DEFAULT_XOR_KEY) -> str:
    """
    Encrypt request payload into edata string:
    1. Convert payload to JSON
    2. UTF-8 encode
    3. XOR with repeating key
    4. Base64 encode
    5. URL encode
    6. Return form body string: edata=<encoded_value>
    """
    if isinstance(payload, BaseModel):
        json_str = payload.model_dump_json(by_alias=True, exclude_none=True)
    elif isinstance(payload, dict):
        json_str = json.dumps(payload, separators=(',', ':'))
    else:
        json_str = str(payload)

    raw_bytes = json_str.encode("utf-8")
    xored = xor_bytes(raw_bytes, key)
    b64_str = base64.b64encode(xored).decode("ascii")
    url_encoded = urllib.parse.quote(b64_str)
    return f"edata={url_encoded}"


def decrypt_response(raw_body: Union[str, bytes], key: str = DEFAULT_XOR_KEY) -> Union[Dict[str, Any], Any]:
    """
    Decrypt server response string/bytes:
    1. Check if raw body is plain JSON first (graceful fallback).
    2. URL decode.
    3. Base64 decode.
    4. XOR with repeating key.
    5. UTF-8 decode.
    6. Parse JSON.
    """
    if isinstance(raw_body, bytes):
        raw_text = raw_body.decode("utf-8", errors="ignore").strip()
    else:
        raw_text = raw_body.strip()

    if not raw_text:
        return {}

    # Check for direct JSON
    if (raw_text.startswith("{") and raw_text.endswith("}")) or (raw_text.startswith("[") and raw_text.endswith("]")):
        try:
            return json.loads(raw_text)
        except Exception:
            pass

    # Attempt decryption pipeline
    try:
        url_decoded = urllib.parse.unquote(raw_text)
        b64_decoded = base64.b64decode(url_decoded)
        xored = xor_bytes(b64_decoded, key)
        decrypted_text = xored.decode("utf-8")
        return json.loads(decrypted_text)
    except Exception:
        # Fallback to direct JSON attempt or raw text return
        try:
            return json.loads(raw_text)
        except Exception:
            return {"raw_content": raw_text}
