# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Selectable creative directions distilled from the official MiniMax H3 skills."""

from __future__ import annotations


DEFAULT_TEMPLATE = "Official H3 · General"

TEMPLATE_BRIEFS = {
    DEFAULT_TEMPLATE: (
        "Use the general MiniMax H3 writing guide without imposing an additional house style. "
        "Infer only the production choices needed to make the user's request coherent."
    ),
    "3D Animation Short · 3D 动画短片": (
        "Shape the result as a compact, character-led 3D animated short with readable silhouettes, "
        "expressive staging, motivated camera movement, clear action beats, and synchronized sound."
    ),
    "Brand Promo · 品牌宣传片": (
        "Shape the result as a polished brand film with a clear product or brand promise, intentional "
        "visual hierarchy, controlled pacing, premium transitions, and brand-safe visible text."
    ),
    "Co-op Game Intro · 合作游戏开场": (
        "Shape the result as an energetic cooperative-game introduction: establish the world, introduce "
        "complementary player roles, reveal the shared objective, and finish on a strong team-action beat."
    ),
    "Hand-drawn Live · 手绘实拍融合": (
        "Blend live-action staging with hand-drawn marks that feel attached to subjects and motion. Keep "
        "the line language consistent, preserve legibility, and synchronize drawn accents with sound cues."
    ),
    "Minimalist Product Ad · 极简产品广告": (
        "Use a restrained product-ad language: uncluttered composition, precise material rendering, a small "
        "palette, deliberate macro details, elegant motion, and minimal but purposeful sound design."
    ),
    "MV Subtitle · 音乐视频字幕": (
        "Treat music, lyrics, editorial rhythm, and on-screen subtitles as one system. Preserve every supplied "
        "lyric verbatim, keep text readable, and align cuts and kinetic typography to musical beats."
    ),
    "Paper Collage Explainer · 纸张拼贴解说": (
        "Use layered paper collage, cut-paper shapes, tactile fibers, simple symbolic compositions, and clear "
        "explanatory progression. Make transitions feel physically assembled rather than digitally dissolved."
    ),
    "Papercraft Stop Motion · 纸艺定格": (
        "Use handcrafted paper models and stop-motion timing with visible folds, cut edges, incremental poses, "
        "practical lighting, and tactile foley while keeping the explanation easy to follow."
    ),
}

PROMPT_TEMPLATES = list(TEMPLATE_BRIEFS)


def template_brief(name: str) -> str:
    try:
        return TEMPLATE_BRIEFS[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported H3 prompt template: {name}") from exc
