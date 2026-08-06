# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

from __future__ import annotations

import unittest

from prompt_builder import MODE_FL2VA, MODE_FULL_REFERENCE, MODE_I2VA, MODE_L2VA, MODE_T2VA
from templates import REQUEST_LEVEL_BASIC, REQUEST_LEVEL_FULL
from validators import clean_model_response, validate_prompt

T2VA = """integrated_multimodal_description: [Shot 1] Live-action, cinematic, a woman walks through a rain-covered street. [Shot 2] At 00:03.000, the camera cuts to a close-up as she opens a taxi door.

overall_soundscape: Rain strikes the pavement while footsteps approach the idling taxi.

non_diegetic_music: N/A"""

I2VA = """For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action, cinematic, the woman shown in <Picture 1> preserves her appearance and position while she turns toward the window.

overall_soundscape: Rain taps steadily against the window.

non_diegetic_music: N/A"""

FL2VA = """How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 1) aligns with the 8.00-second mark of the target video.

integrated_multimodal_description: [Shot 1] Live-action, cinematic, the cyclist begins from Picture 1 and continuously opens the umbrella until reaching Picture 2.

overall_soundscape: Rain falls steadily as the umbrella opens with a metallic click.

non_diegetic_music: N/A"""

L2VA = """How the reference pictures align with the target video — <Picture 1> (from [Shot 2]) aligns with the 6.00-second mark of the target video.

integrated_multimodal_description: [Shot 1] Live-action, cinematic, a glass begins to tip from a table. [Shot 2] At 00:03.500, the camera cuts to the floor as the glass breaks and settles into <Picture 1>.

overall_soundscape: The glass scrapes, falls, and breaks with a sharp crash.

non_diegetic_music: A low electronic pulse stops after the impact."""

FULL_REFERENCE = """subject_definitions:
<Subject 1> is the woman in <Picture 1>, with long dark hair and a blue coat.
<Picture 1> is the first frame of [Shot 1], showing the woman beside a train window.

summary:
[reference generation + keyframe completion] The target video follows <Subject 1> from <Picture 1> as she looks through the train window.

retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - her identity, hair, and blue coat are retained.
<Picture 1> ([Shot 1] first frame): fully_preserved - its opening composition is retained.

detailed_description:
The target video uses a cinematic live-action style with soft, cool lighting.
[Shot 1] The scene begins from <Picture 1>. <Subject 1> remains beside the train window in a medium shot, preserving her long dark hair, blue coat, position, and reflection. The camera holds a static composition while she slowly lifts her gaze toward passing lights outside. The train interior remains stable as her reflection moves across the rain-covered glass.

overall_soundscape:
Train wheels produce a steady metallic rhythm while rain taps against the window.

non_diegetic_music:
N/A"""


class ValidatorTests(unittest.TestCase):
    def test_valid_base_modes(self) -> None:
        cases = [
            (T2VA, MODE_T2VA, 8.0),
            (I2VA, MODE_I2VA, 5.17),
            (FL2VA, MODE_FL2VA, 8.0),
            (L2VA, MODE_L2VA, 6.0),
        ]
        for text, mode, duration in cases:
            with self.subTest(mode=mode):
                result = validate_prompt(text, mode, duration)
                self.assertTrue(result.is_valid, result.report())

    def test_full_reference_is_valid_with_length_warning(self) -> None:
        result = validate_prompt(FULL_REFERENCE, MODE_FULL_REFERENCE, 6.0)
        self.assertTrue(result.is_valid, result.report())
        self.assertTrue(any(issue.code == "description_length" for issue in result.warnings))

    def test_full_reference_length_warning_follows_request_level(self) -> None:
        description = "[Shot 1] " + "detail " * 199
        start = FULL_REFERENCE.index("detailed_description:") + len("detailed_description:")
        end = FULL_REFERENCE.index("\noverall_soundscape:")
        prompt = FULL_REFERENCE[:start] + "\n" + description.rstrip() + "\n" + FULL_REFERENCE[end:]
        basic = validate_prompt(prompt, MODE_FULL_REFERENCE, 6.0, request_level=REQUEST_LEVEL_BASIC)
        full = validate_prompt(prompt, MODE_FULL_REFERENCE, 6.0, request_level=REQUEST_LEVEL_FULL)
        self.assertFalse(any(issue.code == "description_length" for issue in basic.warnings), basic.report())
        self.assertTrue(any(issue.code == "description_length" for issue in full.warnings), full.report())

    def test_bad_shot_time_is_rejected(self) -> None:
        bad = T2VA.replace("00:03.000", "00:09.000")
        result = validate_prompt(bad, MODE_T2VA, 8.0)
        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.code == "timestamp_range" for issue in result.errors))

    def test_invalid_timestamp_seconds_are_rejected(self) -> None:
        bad = T2VA.replace("00:03.000", "00:60.000")
        result = validate_prompt(bad, MODE_T2VA, 90.0)
        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.code == "timestamp_format" for issue in result.errors))

    def test_markdown_fence_and_preface_are_cleaned(self) -> None:
        wrapped = "Here is the prompt:\n```text\n" + T2VA + "\n```"
        cleaned = clean_model_response(wrapped, MODE_T2VA)
        self.assertEqual(cleaned, T2VA)


if __name__ == "__main__":
    unittest.main()
