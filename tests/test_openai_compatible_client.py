# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from openai_compatible_client import OpenAICompatibleClient


class FakeResponse:
    def __init__(self) -> None:
        self.headers = {"x-request-id": "req-123"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(
            {
                "model": "test-model",
                "choices": [{"message": {"content": "finished prompt"}}],
                "usage": {"total_tokens": 12},
            }
        ).encode()


class OpenAICompatibleClientTests(unittest.TestCase):
    def test_openai_shape_uses_current_completion_token_field(self) -> None:
        captured = {}

        def fake_urlopen(request, **kwargs):
            captured["request"] = request
            return FakeResponse()

        client = OpenAICompatibleClient(
            provider="OpenAI",
            base_url="https://api.openai.com/v1/",
            api_key="secret",
            require_api_key=True,
            token_field="max_completion_tokens",
            supports_reasoning_effort=True,
        )
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = client.chat(
                model="gpt-test",
                messages=[{"role": "user", "content": "hello"}],
                max_tokens=1234,
                reasoning_effort="low",
            )
        payload = json.loads(captured["request"].data)
        self.assertEqual(payload["max_completion_tokens"], 1234)
        self.assertNotIn("max_tokens", payload)
        self.assertEqual(payload["reasoning_effort"], "low")
        self.assertEqual(captured["request"].headers["Authorization"], "Bearer secret")
        self.assertEqual(result.request_id, "req-123")

    def test_local_server_allows_empty_key_and_omits_reasoning_field(self) -> None:
        captured = {}

        def fake_urlopen(request, **kwargs):
            captured["request"] = request
            return FakeResponse()

        client = OpenAICompatibleClient(
            provider="Local",
            base_url="http://127.0.0.1:11434/v1",
            token_field="max_tokens",
            supports_reasoning_effort=False,
        )
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            client.chat(model="qwen-vl", messages=[], reasoning_effort="high")
        payload = json.loads(captured["request"].data)
        self.assertIn("max_tokens", payload)
        self.assertNotIn("reasoning_effort", payload)
        self.assertNotIn("Authorization", captured["request"].headers)

    def test_openai_requires_key_before_request(self) -> None:
        with self.assertRaisesRegex(ValueError, "api_key"):
            OpenAICompatibleClient(
                provider="OpenAI",
                base_url="https://api.openai.com/v1",
                require_api_key=True,
            )


if __name__ == "__main__":
    unittest.main()
