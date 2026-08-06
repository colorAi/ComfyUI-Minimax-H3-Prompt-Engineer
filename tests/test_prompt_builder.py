# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

from __future__ import annotations

import unittest

import numpy as np

from image_utils import image_tensor_to_data_url
from presets import CreativePresets
from prompt_builder import (
    MODE_FL2VA,
    MODE_FULL_REFERENCE,
    MODE_T2VA,
    ReferenceImage,
    build_messages,
    build_system_prompt,
    build_translation_messages,
)
from templates import (
    PROMPT_TEMPLATES,
    REQUEST_LEVEL_BASIC,
    REQUEST_LEVEL_FULL,
    REQUEST_LEVEL_MEDIUM,
    template_context,
)


class PromptBuilderTests(unittest.TestCase):
    def test_text_request_contains_duration_and_presets(self) -> None:
        messages = build_messages(
            mode=MODE_T2VA,
            user_request="三个镜头，雨夜出租车。",
            duration=8.0,
            reference_context="",
            presets=CreativePresets(lighting="Neon Night", camera_motion="Tracking Shot"),
            reference_images=[],
            image_max_side=512,
        )
        user = messages[1]["content"]
        self.assertIsInstance(user, str)
        self.assertIn("8.00 seconds", user)
        self.assertIn("Lighting: Neon Night", user)
        self.assertIn("Camera motion: Tracking Shot", user)
        self.assertIn("三个镜头", user)

    def test_multimodal_request_labels_images(self) -> None:
        image = np.zeros((1, 32, 32, 3), dtype=np.float32)
        messages = build_messages(
            mode=MODE_FL2VA,
            user_request="从第一张图自然过渡到第二张图。",
            duration=8.0,
            reference_context="",
            presets=CreativePresets(),
            reference_images=[
                ReferenceImage("<Picture 1>", "first frame", image),
                ReferenceImage("<Picture 2>", "last frame", image),
            ],
            image_max_side=512,
        )
        content = messages[1]["content"]
        self.assertIsInstance(content, list)
        self.assertEqual(sum(part["type"] == "image_url" for part in content), 2)
        self.assertIn("<Picture 1>", content[1]["text"])

    def test_image_encoding(self) -> None:
        image = np.ones((1, 16, 16, 3), dtype=np.float32)
        data_url = image_tensor_to_data_url(image, max_side=512)
        self.assertTrue(data_url.startswith("data:image/jpeg;base64,"))

    def test_selected_template_is_in_system_and_user_context(self) -> None:
        template = "Minimalist Product Ad · 极简产品广告"
        self.assertIn(template, PROMPT_TEMPLATES)
        messages = build_messages(
            mode=MODE_T2VA,
            user_request="A perfume bottle rotates in a studio.",
            duration=5.17,
            template=template,
        )
        self.assertIn(template, messages[0]["content"])
        self.assertIn("restrained product-ad language", messages[0]["content"])
        self.assertIn(template, messages[1]["content"])

    def test_request_levels_add_progressively_more_runtime_guidance(self) -> None:
        template = "Papercraft Stop Motion · 纸艺定格"
        basic = template_context(template, REQUEST_LEVEL_BASIC)
        medium = template_context(template, REQUEST_LEVEL_MEDIUM)
        full = template_context(template, REQUEST_LEVEL_FULL)
        self.assertLess(len(basic), len(medium))
        self.assertLess(len(medium), len(full))
        self.assertIn("production-ready H3 prompt", medium)
        self.assertIn("Final quality control", full)
        self.assertIn("visible folds", full)

    def test_request_levels_scale_guide_payload_and_output_density(self) -> None:
        systems = {
            level: build_system_prompt(MODE_FULL_REFERENCE, request_level=level)
            for level in (REQUEST_LEVEL_BASIC, REQUEST_LEVEL_MEDIUM, REQUEST_LEVEL_FULL)
        }
        self.assertLess(len(systems[REQUEST_LEVEL_BASIC]), len(systems[REQUEST_LEVEL_MEDIUM]))
        self.assertLess(len(systems[REQUEST_LEVEL_MEDIUM]), len(systems[REQUEST_LEVEL_FULL]))
        self.assertGreater(len(systems[REQUEST_LEVEL_FULL]), len(systems[REQUEST_LEVEL_BASIC]) * 3)
        self.assertIn("Target 180–260 English words", systems[REQUEST_LEVEL_BASIC])
        self.assertIn("Target 280–380 English words", systems[REQUEST_LEVEL_MEDIUM])
        self.assertIn("Target 350–500 English words", systems[REQUEST_LEVEL_FULL])
        self.assertNotIn("# Full-Reference Mode Rewrite Output Format Guide", systems[REQUEST_LEVEL_BASIC])
        self.assertNotIn("# Full-Reference Mode Rewrite Output Format Guide", systems[REQUEST_LEVEL_MEDIUM])
        self.assertIn("# Full-Reference Mode Rewrite Output Format Guide", systems[REQUEST_LEVEL_FULL])

    def test_translation_prompt_preserves_h3_contract_tokens(self) -> None:
        messages = build_translation_messages("integrated_multimodal_description: [Shot 1] Test")
        system = messages[0]["content"]
        self.assertIn("Simplified Chinese", system)
        self.assertIn("schema field names", system)
        self.assertIn("<Picture N>", system)
        self.assertEqual(messages[1]["role"], "user")


if __name__ == "__main__":
    unittest.main()
