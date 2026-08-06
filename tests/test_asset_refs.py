# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

from __future__ import annotations

import unittest

import numpy as np

from asset_refs import AssetBundle


class AssetReferenceTests(unittest.TestCase):
    @staticmethod
    def _video(frames: int = 24) -> np.ndarray:
        return np.zeros((frames, 8, 8, 3), dtype=np.float32)

    @staticmethod
    def _audio(seconds: float = 2.0) -> dict:
        sample_rate = 16000
        return {
            "waveform": np.zeros((1, 2, round(sample_rate * seconds)), dtype=np.float32),
            "sample_rate": sample_rate,
        }

    def test_autogrow_order_is_numeric_and_reindexed(self) -> None:
        first = self._video()
        second = self._video()
        bundle = AssetBundle.from_autogrow(
            ref_videos={"ref_video_2": second, "ref_video_1": first},
        )
        self.assertIs(bundle.ref_videos["ref_video_1"], first)
        self.assertIs(bundle.ref_videos["ref_video_2"], second)
        self.assertEqual(bundle.resolve_text("先用@视频2，再回到 @video1"), "先用<Video 2>，再回到 <Video 1>")

    def test_video_soundtrack_and_standalone_audio_follow_native_h3_order(self) -> None:
        soundtrack = self._audio(3.0)
        standalone = self._audio(4.0)
        bundle = AssetBundle.from_autogrow(
            ref_videos={"ref_video_1": self._video()},
            ref_video_audios={"ref_video_audio_1": soundtrack},
            ref_audios={"ref_audio_1": standalone},
        )
        self.assertEqual(
            bundle.resolve_text("配套声用@视频音频1，独立音乐用@音频1"),
            "配套声用<Audio 1>，独立音乐用<Audio 2>",
        )
        self.assertIn("@音频1 / @audio1 -> <Audio 2>", bundle.context_text())

    def test_missing_alias_is_rejected_before_generation(self) -> None:
        bundle = AssetBundle.from_autogrow(ref_images={"ref_image_1": self._video(1)})
        with self.assertRaisesRegex(ValueError, "no connected"):
            bundle.resolve_text("让 @图像2 开始移动")
        with self.assertRaisesRegex(ValueError, "available picture count is 1"):
            bundle.resolve_text("让 <Picture 2> 开始移动")

    def test_orphan_video_soundtrack_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "same-numbered reference video"):
            AssetBundle.from_autogrow(ref_video_audios={"ref_video_audio_1": self._audio()})

    def test_video_samples_keep_video_label(self) -> None:
        video = np.broadcast_to(
            np.arange(48, dtype=np.float32)[:, None, None, None],
            (48, 8, 8, 3),
        ).copy()
        bundle = AssetBundle.from_autogrow(ref_videos={"ref_video_1": video})
        samples = bundle.vision_references(max_video_samples=3)
        self.assertEqual(len(samples), 3)
        self.assertTrue(all(item.label.startswith("<Video 1>") for item in samples))
        self.assertEqual([float(item.image.mean()) for item in samples], [0.0, 24.0, 47.0])


if __name__ == "__main__":
    unittest.main()
