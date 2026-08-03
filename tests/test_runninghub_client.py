from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from runninghub_client import SITE_CHINA, SITE_GLOBAL, RunningHubClient, RunningHubError


class FakeResponse:
    def __init__(self, payload: dict, headers: dict | None = None) -> None:
        self.payload = json.dumps(payload).encode("utf-8")
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self.payload


class RunningHubClientTests(unittest.TestCase):
    def setUp(self) -> None:
        RunningHubClient._models_cache.clear()

    def test_chat_extracts_openai_response(self) -> None:
        response = {
            "model": "qwen/qwen3.6-plus",
            "choices": [{"message": {"role": "assistant", "content": "finished prompt"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 3},
        }
        with patch("urllib.request.urlopen", return_value=FakeResponse(response, {"x-request-id": "req-1"})):
            client = RunningHubClient("secret")
            result = client.chat(model="qwen/qwen3.6-plus", messages=[{"role": "user", "content": "hi"}])
        self.assertEqual(result.content, "finished prompt")
        self.assertEqual(result.request_id, "req-1")

    def test_chat_requires_api_key_before_request(self) -> None:
        with self.assertRaises(RunningHubError) as caught:
            RunningHubClient("").chat(model="test", messages=[])
        self.assertEqual(caught.exception.code, "auth_apikey_missing")

    def test_public_models_are_parsed(self) -> None:
        response = {
            "object": "list",
            "data": [
                {
                    "id": "vision/model",
                    "context_length": 1000,
                    "capabilities": {"vision": True},
                    "pricing": {},
                }
            ],
        }
        with patch("urllib.request.urlopen", return_value=FakeResponse(response)):
            models = RunningHubClient.list_models(force_refresh=True)
        self.assertEqual(models[0].id, "vision/model")
        self.assertTrue(models[0].supports_vision)

    def test_empty_public_model_list_is_rejected(self) -> None:
        with (
            patch("urllib.request.urlopen", return_value=FakeResponse({"object": "list", "data": []})),
            self.assertRaisesRegex(RunningHubError, "usable model entries"),
        ):
            RunningHubClient.list_models(force_refresh=True)

    def test_site_maps_to_expected_base_url(self) -> None:
        self.assertEqual(RunningHubClient.base_url_for_site(SITE_GLOBAL), "https://llm.runninghub.ai/v1")
        self.assertEqual(RunningHubClient.base_url_for_site(SITE_CHINA), "https://llm.runninghub.cn/v1")

    def test_model_cache_is_isolated_by_site(self) -> None:
        global_response = {"data": [{"id": "global/model"}]}
        china_response = {"data": [{"id": "china/model"}]}
        with patch("urllib.request.urlopen", side_effect=[FakeResponse(global_response), FakeResponse(china_response)]):
            global_models = RunningHubClient.list_models(base_url="https://llm.runninghub.ai/v1")
            china_models = RunningHubClient.list_models(base_url="https://llm.runninghub.cn/v1")
        self.assertEqual([item.id for item in global_models], ["global/model"])
        self.assertEqual([item.id for item in china_models], ["china/model"])


if __name__ == "__main__":
    unittest.main()
