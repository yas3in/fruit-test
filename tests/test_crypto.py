"""Unit tests for XOR encryption, Base64, and payload serialization."""

import base64
import json
import urllib.parse
import unittest
from fruitcraft_bot.api.crypto import DEFAULT_XOR_KEY, decrypt_response, encrypt_payload, xor_bytes


class TestCrypto(unittest.TestCase):
    def test_xor_bytes_roundtrip(self):
        original = b"Hello, FruitCraft World!"
        key = "ali1343faraz1055antler288based"

        encrypted = xor_bytes(original, key)
        self.assertNotEqual(encrypted, original)
        decrypted = xor_bytes(encrypted, key)
        self.assertEqual(decrypted, original)

    def test_encrypt_payload_structure(self):
        payload = {"restore_key": "secret123", "os_type": 2}
        result = encrypt_payload(payload, DEFAULT_XOR_KEY)

        self.assertTrue(result.startswith("edata="))
        encoded_val = result.replace("edata=", "")

        unquoted = urllib.parse.unquote(encoded_val)
        b64_dec = base64.b64decode(unquoted)
        xored = xor_bytes(b64_dec, DEFAULT_XOR_KEY)
        decrypted_str = xored.decode("utf-8")

        parsed = json.loads(decrypted_str)
        self.assertEqual(parsed["restore_key"], "secret123")
        self.assertEqual(parsed["os_type"], 2)

    def test_decrypt_response_plain_json_fallback(self):
        raw_json = '{"status": true, "data": {"gold": 1000}}'
        res = decrypt_response(raw_json)
        self.assertTrue(res["status"])
        self.assertEqual(res["data"]["gold"], 1000)

    def test_decrypt_response_encrypted_roundtrip(self):
        data = {"status": True, "data": {"player": "Tester"}, "q": "sample_q_123"}
        json_bytes = json.dumps(data).encode("utf-8")
        xored = xor_bytes(json_bytes, DEFAULT_XOR_KEY)
        b64 = base64.b64encode(xored).decode("ascii")
        url_enc = urllib.parse.quote(b64)

        res = decrypt_response(url_enc, DEFAULT_XOR_KEY)
        self.assertTrue(res["status"])
        self.assertEqual(res["q"], "sample_q_123")
        self.assertEqual(res["data"]["player"], "Tester")


if __name__ == "__main__":
    unittest.main()
