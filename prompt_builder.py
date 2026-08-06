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
    from .templates import DEFAULT_TEMPLATE, template_brief
except ImportError:  # Allows direct imports in local tests.
    from image_utils import image_url_part
    from presets import CreativePresets
    from templates import DEFAULT_TEMPLATE, template_brief


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


def _mode_contract(code: str, duration: float) -> str:
    duration_text = f"{duration:.2f}"
    contracts = {
        "T2VA": (
            "This is a T2VA task. The response must begin directly with "
            "integrated_multimodal_description and contain exactly the three base fields."
        ),
        "I2VA": (
            "This is an I2VA task. <Picture 1> is the first frame at 0.00 seconds and belongs to "
            "[Shot 1]. Use the exact I2VA alignment instruction from the guide."
        ),
        "FL2VA": (
            f"This is an FL2VA task. <Picture 1> is the first frame and <Picture 2> is the final "
            f"frame at {duration_text} seconds. Use the exact FL2VA alignment instruction, with the "
            "actual final shot number. Prefer a single continuous shot unless the user explicitly "
            "requests cuts."
        ),
        "L2VA": (
            f"This is an L2VA task. <Picture 1> is the final frame at {duration_text} seconds. Use the "
            "exact L2VA alignment instruction with the actual final shot number and make the action "
            "converge naturally on that frame."
        ),
        "FULL_REFERENCE": (
            "This is a full-reference task. Return exactly the six full-reference sections in the "
            "specified order. Define and consistently reuse every reference label."
        ),
    }
    return contracts[code]


@lru_cache(maxsize=64)
def build_system_prompt(mode: str, template: str = DEFAULT_TEMPLATE) -> str:
    code = mode_code(mode)
    guide_text = get_base_guide()
    if code == "FULL_REFERENCE":
        guide_text += "\n\n--- FULL-REFERENCE GUIDE ---\n\n" + get_reference_guide()
    creative_direction = template_brief(template)

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
Creative direction: {creative_direction}
Apply this direction only where the user's explicit request and reference-retention requirements leave room for creative judgment. It never changes the required H3 output schema.

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
) -> str | list[dict[str, Any]]:
    code = mode_code(mode)
    presets = CreativePresets.from_value(presets)
    images = reference_images or []
    constraints = presets.active_constraints()

    metadata = [
        f"Task mode: {code}",
        f"Effective target video duration: {duration:.2f} seconds",
        f"Selected creative template: {template}",
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
    return [
        {"role": "system", "content": build_system_prompt(mode, template)},
        {"role": "user", "content": build_user_content(**kwargs)},
    ]


def build_repair_messages(
    *,
    mode: str,
    duration: float,
    previous_response: str,
    validation_report: str,
    template: str = DEFAULT_TEMPLATE,
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
        {"role": "system", "content": build_system_prompt(mode, template)},
        {"role": "user", "content": repair_request},
    ]
