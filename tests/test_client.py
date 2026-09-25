"""Unit tests for FruitCraft API Client."""

import unittest
from unittest.mock import AsyncMock, patch
from fruitcraft_bot.api.client import FruitCraftAPIClient
from fruitcraft_bot.api.crypto import DEFAULT_XOR_KEY, encrypt_payload
from fruitcraft_bot.api.errors import FruitCraftError
from fruitcraft_bot.api.models import PlayerLoadRequest


class TestClient(unittest.IsolatedAsyncioTestCase):
    async def test_client_request_successful(self):
        client = FruitCraftAPIClient(passport="pass_abc")

        mock_payload = {"status": True, "data": {"player": {"id": "1", "name": "FruitKing"}}, "code": 0}
        mock_body = encrypt_payload(mock_payload, DEFAULT_XOR_KEY).replace("edata=", "").encode("utf-8")

        with patch.object(client, "_post_urllib_fallback", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = (200, mock_body, {})

            req = PlayerLoadRequest(restore_key="key123")
            resp = await client.request("player/load", req)

            self.assertTrue(resp.status)
            self.assertIsInstance(resp.data, dict)
            self.assertEqual(resp.data["player"]["name"], "FruitKing")

        await client.close()

    async def test_client_error_handling(self):
        client = FruitCraftAPIClient(max_retries=0)

        mock_error = {"status": False, "code": 101, "message": "Invalid Restore Key"}
        mock_body = encrypt_payload(mock_error, DEFAULT_XOR_KEY).replace("edata=", "").encode("utf-8")

        with patch.object(client, "_post_urllib_fallback", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = (200, mock_body, {})

            with self.assertRaises(FruitCraftError) as cm:
                await client.request("player/load", {"restore_key": "bad"})

            self.assertEqual(cm.exception.code, 101)

        await client.close()


if __name__ == "__main__":
    unittest.main()
