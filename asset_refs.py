# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Deterministic MiniMax H3 asset numbering and @reference expansion."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

try:
    from .prompt_builder import ReferenceImage
except ImportError:  # Allows direct imports in local tests.
    from prompt_builder import ReferenceImage


_INDEX_SUFFIX = re.compile(r"(\d+)$")
_ALIAS = re.compile(
    r"[@＠](视频音频|影片音频|video[_ -]?audio|videoaudio|图像|图片|image|img|视频|影片|video|音频|声音|audio)\s*(\d+)",
    re.IGNORECASE,
)
_NATIVE_REF = re.compile(r"<(Picture|Video|Audio)\s+(\d+)>", re.IGNORECASE)


def _sort_key(item: tuple[str, Any]) -> tuple[int, str]:
    name = str(item[0])
    match = _INDEX_SUFFIX.search(name)
    return (int(match.group(1)) if match else 10**9, name)


def _connected(values: dict[str, Any] | None) -> list[tuple[str, Any]]:
    return sorted(
        ((str(name), value) for name, value in (values or {}).items() if value is not None),
        key=_sort_key,
    )


def _suffix(name: str) -> str:
    match = _INDEX_SUFFIX.search(name)
    return match.group(1) if match else name


def _duration_seconds(audio: Any) -> float | None:
    if not isinstance(audio, dict):
        return None
    waveform = audio.get("waveform")
    sample_rate = audio.get("sample_rate")
    shape = getattr(waveform, "shape", None)
    if not shape or not isinstance(sample_rate, (int, float)) or sample_rate <= 0:
        return None
    return float(shape[-1]) / float(sample_rate)


def _video_frame_count(video: Any) -> int:
    shape = getattr(video, "shape", None)
    if not shape or len(shape) != 4:
        raise ValueError("Reference videos must be IMAGE batches with shape [frames,H,W,C]")
    return int(shape[0])


def _sample_indices(frame_count: int, maximum: int) -> list[int]:
    if frame_count <= 0:
        return []
    count = min(maximum, frame_count)
    if count == 1:
        return [0]
    return [round(index * (frame_count - 1) / (count - 1)) for index in range(count)]


@dataclass(slots=True)
class AssetBundle:
    """Connected refs normalized to the exact presentation order used by ComfyUI's H3 node."""

    ref_images: dict[str, Any] = field(default_factory=dict)
    ref_videos: dict[str, Any] = field(default_factory=dict)
    ref_video_audios: dict[str, Any] = field(default_factory=dict)
    ref_audios: dict[str, Any] = field(default_factory=dict)
    alias_to_native: dict[tuple[str, int], str] = field(default_factory=dict)
    manifest_lines: list[str] = field(default_factory=list)
    native_counts: dict[str, int] = field(default_factory=lambda: {"picture": 0, "video": 0, "audio": 0})

    @property
    def has_references(self) -> bool:
        return bool(self.ref_images or self.ref_videos or self.ref_video_audios or self.ref_audios)

    @property
    def has_audio(self) -> bool:
        return bool(self.ref_video_audios or self.ref_audios)

    @classmethod
    def from_autogrow(
        cls,
        *,
        ref_images: dict[str, Any] | None = None,
        ref_videos: dict[str, Any] | None = None,
        ref_video_audios: dict[str, Any] | None = None,
        ref_audios: dict[str, Any] | None = None,
    ) -> AssetBundle:
        bundle = cls()

        for index, (source_name, image) in enumerate(_connected(ref_images), start=1):
            bundle.ref_images[f"ref_image_{index}"] = image
            native = f"<Picture {index}>"
            bundle.alias_to_native[("picture", index)] = native
            bundle.manifest_lines.append(f"@图像{index} / @image{index} -> {native} ({source_name})")

        soundtrack_by_suffix = {_suffix(name): audio for name, audio in _connected(ref_video_audios)}
        used_soundtracks: set[str] = set()
        audio_number = 0
        for index, (source_name, video) in enumerate(_connected(ref_videos), start=1):
            _video_frame_count(video)
            bundle.ref_videos[f"ref_video_{index}"] = video
            native = f"<Video {index}>"
            bundle.alias_to_native[("video", index)] = native
            bundle.manifest_lines.append(f"@视频{index} / @video{index} -> {native} ({source_name})")

            source_suffix = _suffix(source_name)
            soundtrack = soundtrack_by_suffix.get(source_suffix)
            if soundtrack is not None:
                audio_number += 1
                used_soundtracks.add(source_suffix)
                audio_native = f"<Audio {audio_number}>"
                bundle.ref_video_audios[f"ref_video_audio_{index}"] = soundtrack
                bundle.alias_to_native[("video_audio", index)] = audio_native
                bundle.manifest_lines.append(
                    f"@视频音频{index} / @video_audio{index} -> {audio_native} (soundtrack paired with {native})"
                )

        unused_soundtracks = sorted(
            set(soundtrack_by_suffix) - used_soundtracks,
            key=lambda value: int(value) if value.isdigit() else 10**9,
        )
        if unused_soundtracks:
            joined = ", ".join(unused_soundtracks)
            raise ValueError(
                "Reference video audio must be connected to the same-numbered reference video; "
                f"no matching video was found for suffix(es): {joined}"
            )

        for index, (source_name, audio) in enumerate(_connected(ref_audios), start=1):
            audio_number += 1
            bundle.ref_audios[f"ref_audio_{index}"] = audio
            native = f"<Audio {audio_number}>"
            bundle.alias_to_native[("audio", index)] = native
            duration = _duration_seconds(audio)
            detail = f", {duration:.2f}s" if duration is not None else ""
            bundle.manifest_lines.append(f"@音频{index} / @audio{index} -> {native} ({source_name}{detail})")

        bundle.native_counts = {
            "picture": len(bundle.ref_images),
            "video": len(bundle.ref_videos),
            "audio": audio_number,
        }
        return bundle

    def context_text(self) -> str:
        if not self.manifest_lines:
            return "Connected asset manifest: none."
        return (
            "Connected asset manifest (aliases have already been converted to the native H3 labels below):\n- "
            + "\n- ".join(self.manifest_lines)
            + "\nVideo soundtracks are numbered as H3 audio references before standalone audio, matching ComfyUI exactly."
        )

    @staticmethod
    def _alias_kind(raw: str) -> str:
        key = raw.lower().replace("_", "").replace("-", "").replace(" ", "")
        if key in {"视频音频", "影片音频", "videoaudio"}:
            return "video_audio"
        if key in {"图像", "图片", "image", "img"}:
            return "picture"
        if key in {"视频", "影片", "video"}:
            return "video"
        return "audio"

    def resolve_text(self, text: str, *, validate_native: bool = True) -> str:
        """Expand friendly aliases and reject labels that do not have a connected asset."""

        def replace_alias(match: re.Match[str]) -> str:
            kind = self._alias_kind(match.group(1))
            index = int(match.group(2))
            native = self.alias_to_native.get((kind, index))
            if native is None:
                label = {
                    "picture": "图像",
                    "video": "视频",
                    "video_audio": "视频音频",
                    "audio": "独立音频",
                }[kind]
                raise ValueError(f"{match.group(0)} has no connected {label}{index} material")
            return native

        resolved = _ALIAS.sub(replace_alias, text)
        if validate_native:
            for match in _NATIVE_REF.finditer(resolved):
                kind = match.group(1).lower()
                index = int(match.group(2))
                if index < 1 or index > self.native_counts[kind]:
                    raise ValueError(
                        f"{match.group(0)} does not match the connected assets; available {kind} count is "
                        f"{self.native_counts[kind]}"
                    )
        return resolved

    def vision_references(self, *, max_video_samples: int = 3, fps: float = 24.0) -> list[ReferenceImage]:
        """Return ref images and sparse video frames for multimodal LLM inspection."""
        references: list[ReferenceImage] = []
        for index, image in enumerate(self.ref_images.values(), start=1):
            references.append(
                ReferenceImage(f"<Picture {index}>", "connected full-reference image", image[:1])
            )
        for index, video in enumerate(self.ref_videos.values(), start=1):
            frame_count = _video_frame_count(video)
            sample_indices = _sample_indices(frame_count, max_video_samples)
            for sample_number, frame_index in enumerate(sample_indices, start=1):
                references.append(
                    ReferenceImage(
                        f"<Video {index}> sample {sample_number}/{len(sample_indices)}",
                        f"sampled frame at {frame_index / fps:.2f}s; it remains part of <Video {index}>",
                        video[frame_index : frame_index + 1],
                    )
                )
        return references


def keyframe_bundle(*, first_frame: Any = None, last_frame: Any = None) -> AssetBundle:
    """Build the alias/native-label plan used by MiniMaxH3ImageToVideo."""
    bundle = AssetBundle()
    images: list[tuple[str, Any, str]] = []
    if first_frame is not None:
        images.append(("first_frame", first_frame, "exact first frame at 0.00 seconds"))
    if last_frame is not None:
        images.append(("last_frame", last_frame, "exact final frame at the effective duration"))
    for index, (source_name, image, role) in enumerate(images, start=1):
        native = f"<Picture {index}>"
        bundle.alias_to_native[("picture", index)] = native
        bundle.manifest_lines.append(f"@图像{index} / @image{index} -> {native} ({source_name}; {role})")
        bundle.ref_images[f"ref_image_{index}"] = image
    bundle.native_counts = {"picture": len(images), "video": 0, "audio": 0}
    return bundle
