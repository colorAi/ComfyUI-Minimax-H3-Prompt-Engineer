# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Build strict system/user messages from the two MiniMax H3 writing guides."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from .image_utils import image_url_part
    from .presets import CreativePresets
    from .templates import (
        DEFAULT_TEMPLATE,
        REQUEST_LEVEL_BASIC,
        REQUEST_LEVEL_FULL,
        REQUEST_LEVEL_MEDIUM,
        template_context,
    )
except ImportError:  # Allows direct imports in local tests.
    from image_utils import image_url_part
    from presets import CreativePresets
    from templates import (
        DEFAULT_TEMPLATE,
        REQUEST_LEVEL_BASIC,
        REQUEST_LEVEL_FULL,
        REQUEST_LEVEL_MEDIUM,
        template_context,
    )


MODE_T2VA = "T2VA · Text to Audiovisual"
MODE_I2VA = "I2VA · First Frame to Audiovisual"
MODE_FL2VA = "FL2VA · First and Last Frames to Audiovisual"
MODE_L2VA = "L2VA · Last Frame to Audiovisual"
MODE_FULL_REFERENCE = "FULL_REFERENCE · Full Reference"

TASK_MODES = [MODE_T2VA, MODE_I2VA, MODE_FL2VA, MODE_L2VA, MODE_FULL_REFERENCE]

MODE_CODES = {
    MODE_T2VA: "T2VA",
    MODE_I2VA: "I2VA",
    MODE_FL2VA: "FL2VA",
    MODE_L2VA: "L2VA",
    MODE_FULL_REFERENCE: "FULL_REFERENCE",
    "T2VA": "T2VA",
    "I2VA": "I2VA",
    "FL2VA": "FL2VA",
    "L2VA": "L2VA",
    "FULL_REFERENCE": "FULL_REFERENCE",
}


def mode_code(mode: str) -> str:
    try:
        return MODE_CODES[mode]
    except KeyError as exc:
        raise ValueError(f"Unsupported H3 task mode: {mode}") from exc


@dataclass(slots=True)
class ReferenceImage:
    label: str
    role: str
    image: Any


@lru_cache(maxsize=2)
def _read_guide(filename: str) -> str:
    path = Path(__file__).resolve().parent / filename
    return path.read_text(encoding="utf-8")


def get_base_guide() -> str:
    return _read_guide("VIDEO_PROMPT_WRITING_GUIDE_base_en.md")


def get_reference_guide() -> str:
    return _read_guide("VIDEO_PROMPT_WRITING_GUIDE_ref_en.md")


COMPACT_BASE_GUIDE = """H3 compact base contract

Return only the final English prompt document. T2VA begins directly with the three fields below. I2VA, FL2VA,
and L2VA first write the exact alignment line supplied in the task contract, followed by one blank line.

Required fields and order:
integrated_multimodal_description: [Shot 1] ...
overall_soundscape: ...
non_diegetic_music: ...

The first shot is `[Shot 1]` with no timestamp. Each later cut is sequential and begins exactly
`[Shot N] At MM:SS.mmm,` at a strictly increasing time inside the effective duration. Describe visible action,
camera behavior, dialogue, and synchronized diegetic sound in the main field. Write dialogue or lyrics exactly as
`<d>[Language] ...</d>`. Summarize ambience, physical sounds, and non-verbal human sounds in
`overall_soundscape`. Use `non_diegetic_music: N/A` when no audience-only score is requested or needed.

For keyframe modes, preserve identity, clothing, composition, colors, objects, and spatial relationships from the
connected picture. I2VA develops forward from Picture 1; FL2VA moves continuously from Picture 1 to Picture 2;
L2VA builds a plausible earlier state and converges exactly on Picture 1 at the end."""


COMPACT_REFERENCE_GUIDE = """H3 compact full-reference contract

Return exactly these six English sections in order, with no text before `subject_definitions:`:
subject_definitions:
summary:
retention_analysis:
detailed_description:
overall_soundscape:
non_diegetic_music:

Define every used `<Subject N>`, `<Picture N>`, `<Video N>`, and `<Audio N>` label once in
`subject_definitions`, preserving the source role and the attributes that matter. Begin `summary` with one or more
valid task types joined by ` + ` inside brackets: `keyframe completion`, `reference generation`, `video editing`,
`video continuation`, `audio reuse`, or `audio reference`.

Write one `retention_analysis` line for every defined reference. Visible references use `fully_preserved`,
`partially_preserved`, `attribute_transfer`, or `weak_reference`; audio references use `fully_copy`,
`partially_copy`, `reference`, or `weak_reference`. Follow each marker with ` - ` and a concrete explanation.

In `detailed_description`, establish the target style briefly, then describe playback order. `[Shot 1]` has no
timestamp; every later cut begins exactly `[Shot N] At MM:SS.mmm,` at a strictly increasing time inside the target
duration. Reuse reference labels wherever their roles take effect. Preserve dialogue and lyrics exactly inside
`<d>[Language] ...</d>`. Summarize ambience and physical sounds in `overall_soundscape`; describe audience-only
music in `non_diegetic_music`, or write `N/A` when none is requested."""


MEDIUM_GUIDE_EXTENSION = """Medium H3 production guidance

- Give the target a clear setup, development, and payoff that fit the effective duration.
- Preserve subject identity, wardrobe, props, environment layout, lighting direction, screen direction, and object
  state across the timeline.
- Describe only camera framing and movement that materially improve action readability; avoid stacked camera labels.
- Give motion visible anticipation, contact, weight, reaction, and settling when appropriate.
- Synchronize ambience, action foley, dialogue, and meaningful music changes without repeating dialogue in the audio
  summary fields.
- Treat reference roles precisely: preserve what the request protects, transfer only requested attributes, and do not
  silently merge or renumber references.
- Preserve exact dialogue, lyrics, brand text, and visible text. Remove contradictions, impossible timing, decorative
  details with no production purpose, and unsupported claims before returning the document."""


def guide_context(mode: str, request_level: str = REQUEST_LEVEL_BASIC) -> str:
    """Select progressively larger H3 guide context for the requested production depth."""
    code = mode_code(mode)
    compact = COMPACT_REFERENCE_GUIDE if code == "FULL_REFERENCE" else COMPACT_BASE_GUIDE
    if request_level == REQUEST_LEVEL_BASIC:
        return compact
    if request_level == REQUEST_LEVEL_MEDIUM:
        return f"{compact}\n\n{MEDIUM_GUIDE_EXTENSION}"
    if request_level == REQUEST_LEVEL_FULL:
        guide = get_base_guide()
        if code == "FULL_REFERENCE":
            guide += "\n\n--- FULL-REFERENCE GUIDE ---\n\n" + get_reference_guide()
        return guide
    raise ValueError(f"Unsupported template request level: {request_level}")


def output_density_contract(mode: str, request_level: str = REQUEST_LEVEL_BASIC) -> str:
    code = mode_code(mode)
    ranges = {
        REQUEST_LEVEL_BASIC: ("compact", "180–260" if code == "FULL_REFERENCE" else "100–180"),
        REQUEST_LEVEL_MEDIUM: ("production-ready", "280–380" if code == "FULL_REFERENCE" else "180–300"),
        REQUEST_LEVEL_FULL: ("maximally detailed", "350–500" if code == "FULL_REFERENCE" else "as needed"),
    }
    try:
        density, target = ranges[request_level]
    except KeyError as exc:
        raise ValueError(f"Unsupported template request level: {request_level}") from exc
    noun = "detailed_description" if code == "FULL_REFERENCE" else "integrated_multimodal_description"
    return (
        f"Write a {density} final document. Target {target} English words in `{noun}`. "
        "Never omit required fields or explicit user instructions. Use one continuous shot unless the user requests "
        "cuts or additional shots are necessary to express distinct events. Do not add decorative events, props, "
        "sound, or camera moves merely to increase detail."
    )


def _mode_contract(code: str, duration: float) -> str:
    duration_text = f"{duration:.2f}"
    contracts = {
        "T2VA": (
            "This is a T2VA task. The response must begin directly with "
            "integrated_multimodal_description and contain exactly the three base fields."
        ),
        "I2VA": (
            "This is an I2VA task. <Picture 1> is the first frame at 0.00 seconds and belongs to [Shot 1]. "
            "The first line must be exactly: For the target video, at 0.00 seconds into the target video, "
            "<Picture 1> (from [Shot 1]) is fully referenced."
        ),
        "FL2VA": (
            f"This is an FL2VA task. <Picture 1> is the first frame and <Picture 2> is the final "
            f"frame at {duration_text} seconds. The first line must be exactly the following, replacing N with the "
            "actual final shot number: How the reference pictures align with the target video — Picture 1 "
            "(from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns "
            f"with the {duration_text}-second mark of the target video. Prefer a single continuous shot unless the "
            "user explicitly requests cuts."
        ),
        "L2VA": (
            f"This is an L2VA task. <Picture 1> is the final frame at {duration_text} seconds. The first line must "
            "be exactly the following, replacing N with the actual final shot number: How the reference pictures "
            "align with the target video — <Picture 1> (from [Shot N]) aligns with the "
            f"{duration_text}-second mark of the target video. Make the action converge naturally on that frame."
        ),
        "FULL_REFERENCE": (
            "This is a full-reference task. Return exactly the six full-reference sections in the "
            "specified order. Define and consistently reuse every reference label."
        ),
    }
    return contracts[code]


@lru_cache(maxsize=64)
def build_system_prompt(
    mode: str,
    template: str = DEFAULT_TEMPLATE,
    request_level: str = REQUEST_LEVEL_BASIC,
) -> str:
    mode_code(mode)
    guide_text = guide_context(mode, request_level)
    creative_direction = template_context(template, request_level)
    density_contract = output_density_contract(mode, request_level)

    return f"""You are Minimax H3 Prompt Engineer, a strict professional rewrite engine.

Your only job is to transform the user's possibly short Chinese or English production request into a complete English MiniMax H3 video prompt that follows the supplied guide exactly.

Non-negotiable behavior:
1. Output only the finished prompt document. Do not add explanations, notes, headings outside the required fields, Markdown fences, or apologies.
2. Write all descriptions in English. Preserve the exact original language, words, and punctuation only for user-provided dialogue or lyrics inside <d>, and for text visibly present in the scene.
3. Never omit user-requested shots. When the user describes Shot 1, Shot 2, or sequential camera cuts, convert every described shot into sequential [Shot N] blocks. [Shot 1] has no timestamp. Every later shot begins with a strictly increasing cut time inside the effective duration.
4. If the user gives cut times, preserve them when valid. If cut times are absent, allocate plausible times according to shot content and the effective duration.
5. Preserve user-provided dialogue, lyrics, visible text, character identities, reference roles, and keyframe relationships exactly. Do not translate dialogue, lyrics, or visible text.
6. Treat every non-Auto node preset listed by the user as a deliberate structured constraint. It overrides conflicting free-form style/camera wording, except that it may never alter exact dialogue, identity, visible text, or reference alignment.
7. Express camera movement naturally within the appropriate shot. Never append a stack of camera labels.
8. Check the complete answer against the required format before returning it.

Selected creative template: {template}
Template request level: {request_level}
Creative direction and production rules:
{creative_direction}
Apply this direction only where the user's explicit request and reference-retention requirements leave room for creative judgment. It never changes the required H3 output schema.

Output density contract:
{density_contract}

The authoritative writing guide follows:

--- GUIDE START ---
{guide_text}
--- GUIDE END ---
"""


def build_user_content(
    *,
    mode: str,
    user_request: str,
    duration: float,
    reference_context: str = "",
    presets: CreativePresets | dict[str, Any] | None = None,
    reference_images: list[ReferenceImage] | None = None,
    image_max_side: int = 1536,
    template: str = DEFAULT_TEMPLATE,
    request_level: str = REQUEST_LEVEL_BASIC,
) -> str | list[dict[str, Any]]:
    code = mode_code(mode)
    presets = CreativePresets.from_value(presets)
    images = reference_images or []
    constraints = presets.active_constraints()

    metadata = [
        f"Task mode: {code}",
        f"Effective target video duration: {duration:.2f} seconds",
        f"Selected creative template: {template}",
        f"Template request level: {request_level}",
        _mode_contract(code, duration),
    ]
    if constraints:
        metadata.append("Structured creative constraints:\n- " + "\n- ".join(constraints))
    else:
        metadata.append(
            "Structured creative constraints: Auto; infer only what is needed from the request and references."
        )
    if reference_context.strip():
        metadata.append("Reference context supplied by the user:\n" + reference_context.strip())

    prefix = "\n\n".join(metadata)
    suffix = (
        "User production request (preserve every requested shot and every exact spoken/visible string):\n"
        + user_request.strip()
    )
    if not images:
        return f"{prefix}\n\n{suffix}"

    content: list[dict[str, Any]] = [{"type": "text", "text": prefix}]
    for item in images:
        content.append(
            {
                "type": "text",
                "text": f"\n{item.label} — {item.role}. Inspect this image carefully and use it only in that role:\n",
            }
        )
        content.append(image_url_part(item.image, max_side=image_max_side))
    content.append({"type": "text", "text": "\n\n" + suffix})
    return content


def build_messages(**kwargs: Any) -> list[dict[str, Any]]:
    mode = kwargs["mode"]
    template = kwargs.get("template", DEFAULT_TEMPLATE)
    request_level = kwargs.get("request_level", REQUEST_LEVEL_BASIC)
    return [
        {"role": "system", "content": build_system_prompt(mode, template, request_level)},
        {"role": "user", "content": build_user_content(**kwargs)},
    ]


def build_repair_messages(
    *,
    mode: str,
    duration: float,
    previous_response: str,
    validation_report: str,
    template: str = DEFAULT_TEMPLATE,
    request_level: str = REQUEST_LEVEL_BASIC,
) -> list[dict[str, Any]]:
    code = mode_code(mode)
    repair_request = f"""The previous response failed deterministic MiniMax H3 format validation.

Task mode: {code}
Effective duration: {duration:.2f} seconds

Validation report:
{validation_report}

Previous response:
--- PREVIOUS RESPONSE START ---
{previous_response}
--- PREVIOUS RESPONSE END ---

Correct every listed error while preserving all scene content, dialogue, lyrics, visible text, reference identities, shot intent, and valid timestamps. Return only the corrected finished prompt document.
"""
    return [
        {"role": "system", "content": build_system_prompt(mode, template, request_level)},
        {"role": "user", "content": repair_request},
    ]


def build_translation_messages(prompt: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Translate the supplied MiniMax H3 prompt into Simplified Chinese for human display. "
                "Keep all schema field names, [Shot N] markers, timestamps, <Subject N>/<Picture N>/<Video N>/"
                "<Audio N> labels, retention markers, and <d>[Language]...</d> blocks exactly unchanged. "
                "Preserve user-supplied dialogue, lyrics, brand text, and visible text verbatim. Translate all other "
                "descriptive prose accurately and completely. Output only the translated prompt document."
            ),
        },
        {"role": "user", "content": prompt},
    ]
