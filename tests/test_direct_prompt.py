# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

from __future__ import annotations

import unittest

from direct_prompt import PROVIDER_DIRECT_RAW, PROVIDER_DIRECT_STRICT, prepare_direct_prompt
from prompt_builder import MODE_FULL_REFERENCE
from templates import REQUEST_LEVEL_BASIC
from tests.test_validators import FULL_REFERENCE


class DirectPromptTests(unittest.TestCase):
    @staticmethod
    def _resolve(text: str) -> str:
        return text.replace("@视频1", "<Video 1>").replace("@图像1", "<Picture 1>")

    def test_pass_through_accepts_plain_prompt_and_resolves_aliases(self) -> None:
        result = prepare_direct_prompt(
            provider=PROVIDER_DIRECT_RAW,
            user_request="移除@视频1的绿幕，背景参考@图像1。",
            resolve_text=self._resolve,
            mode=MODE_FULL_REFERENCE,
            duration=6.0,
            request_level=REQUEST_LEVEL_BASIC,
        )
        self.assertEqual(result.formatted, "移除<Video 1>的绿幕，背景参考<Picture 1>。")
        self.assertTrue(result.is_valid)
        self.assertTrue(result.validation_skipped)
        self.assertTrue(result.validation_report.startswith("SKIPPED"))

    def test_strict_direct_rejects_plain_prompt(self) -> None:
        result = prepare_direct_prompt(
            provider=PROVIDER_DIRECT_STRICT,
            user_request="移除@视频1的绿幕。",
            resolve_text=self._resolve,
            mode=MODE_FULL_REFERENCE,
            duration=6.0,
            request_level=REQUEST_LEVEL_BASIC,
        )
        self.assertFalse(result.is_valid)
        self.assertFalse(result.validation_skipped)
        self.assertIn("full_reference_start", result.validation_report)

    def test_strict_direct_accepts_complete_document(self) -> None:
        result = prepare_direct_prompt(
            provider=PROVIDER_DIRECT_STRICT,
            user_request=FULL_REFERENCE,
            resolve_text=self._resolve,
            mode=MODE_FULL_REFERENCE,
            duration=6.0,
            request_level=REQUEST_LEVEL_BASIC,
        )
        self.assertTrue(result.is_valid, result.validation_report)
        self.assertFalse(result.validation_skipped)


if __name__ == "__main__":
    unittest.main()
