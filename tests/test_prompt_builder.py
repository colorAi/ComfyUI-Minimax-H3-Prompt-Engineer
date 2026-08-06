# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

from __future__ import annotations

import unittest

import numpy as np

from image_utils import image_tensor_to_data_url
from presets import CreativePresets
from prompt_builder import MODE_FL2VA, MODE_T2VA, ReferenceImage, build_messages
from templates import PROMPT_TEMPLATES


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


if __name__ == "__main__":
    unittest.main()
