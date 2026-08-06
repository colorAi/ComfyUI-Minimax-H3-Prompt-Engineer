# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Selectable creative directions distilled from the official MiniMax H3 skills."""

from __future__ import annotations

DEFAULT_TEMPLATE = "Official H3 · General"

REQUEST_LEVEL_BASIC = "Basic · 基础"
REQUEST_LEVEL_MEDIUM = "Medium · 中度"
REQUEST_LEVEL_FULL = "Full · 完整"
REQUEST_LEVELS = [REQUEST_LEVEL_BASIC, REQUEST_LEVEL_MEDIUM, REQUEST_LEVEL_FULL]

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

TEMPLATE_DETAIL_RULES = {
    DEFAULT_TEMPLATE: (
        "Do not impose a genre that the user did not request. Resolve missing production choices conservatively, "
        "keep the visual and audio plan coherent, and prioritize the user's explicit outcome over decorative detail."
    ),
    "3D Animation Short · 3D 动画短片": (
        "Use consistent character proportions, materials, color scripts, and environment scale. Stage poses with "
        "clear anticipation, action, reaction, and settling beats; avoid weightless motion, identity drift, and camera "
        "moves that obscure the performance. Let lighting and foley reinforce each important animated action."
    ),
    "Brand Promo · 品牌宣传片": (
        "Protect product truth, logo geometry, brand colors, packaging, and supplied claims. Build a clear hierarchy "
        "from problem or desire to product proof and hero payoff. Keep visible text brief and readable, use premium "
        "motivated transitions, and never invent product capabilities, awards, prices, or performance metrics."
    ),
    "Co-op Game Intro · 合作游戏开场": (
        "Make each player role visually distinct through silhouette, equipment, movement, and contribution. Establish "
        "the shared objective, escalate a readable threat, show complementary actions rather than isolated hero shots, "
        "and end with a synchronized team payoff that remains legible as gameplay-inspired action."
    ),
    "Hand-drawn Live · 手绘实拍融合": (
        "Anchor drawn marks to tracked subjects, surfaces, and motion so they do not slide or detach. Keep stroke weight, "
        "color language, frame-to-frame jitter, occlusion, and layer order consistent. Use illustration to clarify or "
        "amplify live action without hiding faces, products, dialogue, or important physical interactions."
    ),
    "Minimalist Product Ad · 极简产品广告": (
        "Limit props and palette, preserve generous negative space, and make every camera or object movement serve the "
        "product reveal. Describe material response, reflections, edge light, contact shadows, macro detail, and final "
        "packshot precisely. Avoid clutter, arbitrary particles, excessive cuts, and unsupported marketing claims."
    ),
    "MV Subtitle · 音乐视频字幕": (
        "Preserve supplied lyrics word for word and coordinate editorial beats, performance, typography, and sound. "
        "Specify when each subtitle appears, moves, and clears; maintain contrast, safe margins, and enough reading time. "
        "Do not invent missing lyrics or let kinetic text cover faces and essential action."
    ),
    "Paper Collage Explainer · 纸张拼贴解说": (
        "Keep paper grain, torn or cut edges, shadows, layer depth, and palette consistent. Turn each explanation beat "
        "into one readable visual metaphor, and transition by folding, sliding, tearing, stacking, or replacing physical "
        "paper elements. Avoid photorealistic morphs and overcrowded diagrams."
    ),
    "Papercraft Stop Motion · 纸艺定格": (
        "Describe buildable paper forms, visible folds, tabs, seams, incremental poses, practical lighting, and stable "
        "tabletop geography. Use deliberate stop-motion cadence with small physical discontinuities and tactile foley. "
        "Keep construction, scale, shadows, and prop positions continuous across frames and shots."
    ),
}

MEDIUM_RUNTIME_RULES = """Develop the selected direction into a production-ready H3 prompt.
- Establish a clear beginning, development, and payoff that fit the effective duration.
- Make every shot advance the action or communication goal; avoid decorative shots with no function.
- Keep subject identity, wardrobe, props, environment, lighting direction, and spatial relationships continuous.
- Describe motivated camera framing and movement as part of the visible action.
- Synchronize physical actions, dialogue, environmental sound, foley, and music changes.
- Preserve all connected-reference roles and all exact dialogue, lyrics, brand text, and visible text.
- Prefer concrete visible or audible details over abstract mood labels.
- Before returning, remove contradictions, impossible timing, redundant camera labels, and unsupported claims."""

FULL_RUNTIME_RULES = """Treat this as a complete single-request production workflow, but output only the final H3 prompt document.

Outcome and constraint hierarchy:
- Preserve the user's communication goal, requested events, exact strings, reference relationships, duration, and selected node constraints first.
- Use the selected template as a production grammar, not as permission to replace explicit user intent.
- Do not invent brand facts, product claims, lyrics, dialogue, identities, source-audio words, or visible text.

Beat and shot design:
- Internally organize the duration into setup, development, transition, and payoff beats before writing shots.
- Give every shot a specific visual purpose, entry state, action progression, audio progression, and exit state.
- Allocate cut times by information load and physical action duration. Avoid cuts that interrupt required dialogue, text reading, or reference retention.
- Use a continuous shot when continuity is more important than coverage; use multiple shots only when each angle adds necessary information.

Visual system and continuity:
- Establish the medium, style grammar, palette, material behavior, lighting logic, atmosphere, environment scale, and composition rules early and keep them stable.
- Define important subjects with reusable identity anchors: appearance, proportions, wardrobe, voice, carried objects, and spatial role.
- Track screen direction, eyelines, hand occupancy, prop state, body position, environment layout, light direction, and cause-and-effect across shots.
- For connected materials, distinguish what must be fully preserved, what may be transferred, and what is only weak inspiration. Never silently renumber or merge references.

Motion, camera, and transitions:
- Give motion believable anticipation, acceleration, contact, weight, reaction, and settling where appropriate to the chosen medium.
- Describe camera size, angle, lens feeling, movement direction, amplitude, and speed only when they materially affect the shot.
- Motivate transitions through action, composition, sound, or the selected physical/graphic medium; avoid arbitrary dissolves and effect stacking.
- Keep the main action readable and avoid camera movement that competes with dialogue, product proof, subtitles, or character performance.

Audio and text:
- Build a synchronized sound plan with ambience, action foley, impacts, non-verbal vocal sounds, dialogue, diegetic audio, and non-diegetic music in their correct sections.
- Specify meaningful audio entrances, exits, emphasis points, and carry-over across cuts without duplicating dialogue in the soundscape section.
- Preserve dialogue and lyrics exactly inside language tags. For visible text, preserve spelling and punctuation, state placement and legibility, and allow enough screen time to read it.

Final quality control:
- Verify task-mode schema, section order, reference labels, shot numbering, timestamps, duration bounds, dialogue tags, and required retention markers.
- Remove contradictions, continuity breaks, identity drift, vague adjectives, redundant instructions, impossible simultaneous actions, unsupported claims, and details that cannot be seen or heard.
- Return only the final structured H3 prompt, never the internal plan, checklist, questions, tool instructions, or commentary."""


def template_brief(name: str) -> str:
    try:
        return TEMPLATE_BRIEFS[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported H3 prompt template: {name}") from exc


def template_context(name: str, request_level: str = REQUEST_LEVEL_BASIC) -> str:
    brief = template_brief(name)
    try:
        details = TEMPLATE_DETAIL_RULES[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported H3 prompt template: {name}") from exc
    if request_level == REQUEST_LEVEL_BASIC:
        return brief
    if request_level == REQUEST_LEVEL_MEDIUM:
        return f"{brief}\n\nTemplate-specific rules:\n{details}\n\n{MEDIUM_RUNTIME_RULES}"
    if request_level == REQUEST_LEVEL_FULL:
        return f"{brief}\n\nTemplate-specific rules:\n{details}\n\n{FULL_RUNTIME_RULES}"
    raise ValueError(f"Unsupported template request level: {request_level}")
