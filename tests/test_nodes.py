# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

from nodes import MinimaxH3PromptEngineerRunningHub
from prompt_builder import MODE_T2VA
from runninghub_client import SITE_CHINA, SITE_GLOBAL, ChatResult, ModelInfo
from tests.test_validators import T2VA


class NodeTests(unittest.TestCase):
    @staticmethod
    def _result(content: str, request_id: str) -> ChatResult:
        return ChatResult(
            content=content, usage={"total_tokens": 10}, model="test/model", request_id=request_id, raw={}
        )

    @staticmethod
    def _model(model_id: str = "test/model", *, vision: bool = True) -> ModelInfo:
        return ModelInfo(
            id=model_id,
            context_length=32768,
            capabilities={"vision": vision},
            pricing={},
            raw={},
        )

    def test_auto_repair_revalidates_response(self) -> None:
        node = MinimaxH3PromptEngineerRunningHub()
        invalid = "Here is a nice prompt, but it has no required fields."
        with (
            patch("nodes.RunningHubClient.list_models", return_value=[self._model()]),
            patch("nodes.RunningHubClient.chat", side_effect=[self._result(invalid, "1"), self._result(T2VA, "2")]),
        ):
            output = node.generate(
                runninghub_api_key="secret",
                runninghub_site=SITE_GLOBAL,
                model="test/model",
                custom_model="",
                task_mode=MODE_T2VA,
                user_request="雨夜出租车，两个镜头。",
                duration_seconds=8.0,
                reference_context="",
                temperature=0.2,
                top_p=0.9,
                max_tokens=2048,
                reasoning_effort="none",
                timeout_seconds=120,
                image_max_side=512,
                auto_repair=True,
                strict_validation=True,
            )
        self.assertEqual(output[0], T2VA)
        self.assertTrue(output[1].startswith("PASS"))
        self.assertIn('"phase": "repair"', output[3])

    def test_empty_key_fails_locally(self) -> None:
        node = MinimaxH3PromptEngineerRunningHub()
        with self.assertRaisesRegex(ValueError, "api_key"):
            node.generate(
                runninghub_api_key="",
                runninghub_site=SITE_GLOBAL,
                model="test/model",
                custom_model="",
                task_mode=MODE_T2VA,
                user_request="test",
                duration_seconds=8.0,
                reference_context="",
                temperature=0.2,
                top_p=0.9,
                max_tokens=2048,
                reasoning_effort="none",
                timeout_seconds=120,
                image_max_side=512,
                auto_repair=True,
                strict_validation=True,
            )

    def test_china_site_uses_cn_endpoint(self) -> None:
        node = MinimaxH3PromptEngineerRunningHub()
        with (
            patch("nodes.RunningHubClient.list_models", return_value=[self._model()]),
            patch("nodes.RunningHubClient.chat", return_value=self._result(T2VA, "cn-1")),
        ):
            output = node.generate(
                runninghub_api_key="secret",
                runninghub_site=SITE_CHINA,
                model="test/model",
                custom_model="",
                task_mode=MODE_T2VA,
                user_request="雨夜街道",
                duration_seconds=8.0,
                reference_context="",
                temperature=0.2,
                top_p=0.9,
                max_tokens=2048,
                reasoning_effort="none",
                timeout_seconds=120,
                image_max_side=512,
                auto_repair=True,
                strict_validation=True,
            )
        self.assertIn('"site": "RunningHub China (.cn)"', output[3])
        self.assertIn("https://llm.runninghub.cn/v1/chat/completions", output[3])

    def test_rejects_model_not_available_on_selected_site(self) -> None:
        node = MinimaxH3PromptEngineerRunningHub()
        with (
            patch("nodes.RunningHubClient.list_models", return_value=[self._model("cn/model")]),
            self.assertRaisesRegex(ValueError, "not available"),
        ):
            node.generate(
                runninghub_api_key="secret",
                runninghub_site=SITE_CHINA,
                model="global-only/model",
                custom_model="",
                task_mode=MODE_T2VA,
                user_request="test",
                duration_seconds=8.0,
                reference_context="",
                temperature=0.2,
                top_p=0.9,
                max_tokens=2048,
                reasoning_effort="none",
                timeout_seconds=120,
                image_max_side=512,
                auto_repair=True,
                strict_validation=True,
            )

    def test_fl2va_requires_both_keyframes(self) -> None:
        image = np.zeros((1, 16, 16, 3), dtype=np.float32)
        with self.assertRaisesRegex(ValueError, "both first_frame and last_frame"):
            MinimaxH3PromptEngineerRunningHub._collect_images(
                task_mode="FL2VA · First and Last Frames to Audiovisual",
                first_frame=image,
            )

    def test_full_reference_can_use_textual_asset_context(self) -> None:
        images = MinimaxH3PromptEngineerRunningHub._collect_images(
            task_mode="FULL_REFERENCE · Full Reference",
            reference_context="<Video 1> is the source video to continue.",
        )
        self.assertEqual(images, [])


if __name__ == "__main__":
    unittest.main()
