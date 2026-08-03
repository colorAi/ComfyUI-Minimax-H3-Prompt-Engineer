# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Deterministic structural validators for MiniMax H3 prompt documents."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

try:
    from .prompt_builder import mode_code
except ImportError:  # Allows direct imports in local tests.
    from prompt_builder import mode_code


BASE_FIELDS = [
    "integrated_multimodal_description",
    "overall_soundscape",
    "non_diegetic_music",
]

FULL_REFERENCE_FIELDS = [
    "subject_definitions",
    "summary",
    "retention_analysis",
    "detailed_description",
    "overall_soundscape",
    "non_diegetic_music",
]

SUMMARY_TYPES = {
    "keyframe completion",
    "reference generation",
    "video editing",
    "video continuation",
    "audio reuse",
    "audio reference",
}

VISIBLE_RETENTION_MARKERS = {
    "fully_preserved",
    "partially_preserved",
    "attribute_transfer",
    "weak_reference",
}

AUDIO_RETENTION_MARKERS = {
    "fully_copy",
    "partially_copy",
    "reference",
    "weak_reference",
}


@dataclass(slots=True)
class ValidationIssue:
    level: str
    code: str
    message: str


@dataclass(slots=True)
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [item for item in self.issues if item.level == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [item for item in self.issues if item.level == "warning"]

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def error(self, code: str, message: str) -> None:
        self.issues.append(ValidationIssue("error", code, message))

    def warning(self, code: str, message: str) -> None:
        self.issues.append(ValidationIssue("warning", code, message))

    def report(self) -> str:
        if not self.issues:
            return "PASS — The prompt matches the required MiniMax H3 structure."
        lines = ["FAIL — Structural validation found errors." if self.errors else "PASS WITH WARNINGS."]
        for issue in self.issues:
            lines.append(f"{issue.level.upper()} [{issue.code}] {issue.message}")
        return "\n".join(lines)


def clean_model_response(text: str, mode: str) -> str:
    """Remove common model wrappers without touching document content."""
    cleaned = text.strip().lstrip("\ufeff")
    fence = re.fullmatch(r"```(?:text|markdown|md)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence:
        cleaned = fence.group(1).strip()

    code = mode_code(mode)
    starts = {
        "T2VA": "integrated_multimodal_description:",
        "I2VA": "For the target video, at 0.00 seconds into the target video,",
        "FL2VA": "How the reference pictures align with the target video",
        "L2VA": "How the reference pictures align with the target video",
        "FULL_REFERENCE": "subject_definitions:",
    }
    marker = starts[code]
    position = cleaned.find(marker)
    if 0 < position <= 500:
        cleaned = cleaned[position:]
    if cleaned.rstrip().endswith("```"):
        cleaned = cleaned.rstrip()[:-3]
    return cleaned.strip()


def _extract_sections(text: str, fields: list[str], result: ValidationResult) -> dict[str, str]:
    pattern = re.compile(r"(?m)^(" + "|".join(re.escape(field) for field in fields) + r"):\s*")
    matches = list(pattern.finditer(text))
    found = [match.group(1) for match in matches]
    if found != fields:
        result.error(
            "section_order",
            f"Required section order is {', '.join(fields)}; found {', '.join(found) or 'none'}.",
        )
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.end() : end].strip()
    for field_name in fields:
        if not sections.get(field_name):
            result.error("empty_section", f"Section {field_name} is missing or empty.")
    return sections


def _timestamp_seconds(minutes: str, seconds: str) -> float:
    return int(minutes) * 60 + float(seconds)


def _validate_shots(body: str, duration: float, result: ValidationResult) -> int:
    shots = list(re.finditer(r"\[Shot\s+(\d+)\]", body))
    if not shots:
        result.error("missing_shot", "The main description must contain [Shot 1].")
        return 0
    numbers = [int(match.group(1)) for match in shots]
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        result.error("shot_sequence", f"Shot markers must be sequential {expected}; found {numbers}.")

    first_tail = body[shots[0].end() : shots[0].end() + 32]
    if re.match(r"\s*At\s+\d", first_tail):
        result.error("shot1_timestamp", "[Shot 1] must not have a timestamp.")

    previous = 0.0
    for shot_index, shot in enumerate(shots[1:], start=2):
        tail = body[shot.end() : shot.end() + 48]
        timestamp = re.match(r"\s+At\s+(\d{2}):(\d{2}\.\d{3}),", tail)
        if not timestamp:
            result.error(
                "shot_timestamp",
                f"[Shot {shot_index}] must begin with 'At MM:SS.mmm,'.",
            )
            continue
        if float(timestamp.group(2)) >= 60:
            result.error(
                "timestamp_format",
                f"[Shot {shot_index}] uses an invalid seconds component; MM:SS.mmm requires SS below 60.",
            )
            continue
        value = _timestamp_seconds(timestamp.group(1), timestamp.group(2))
        if value <= previous:
            result.error("timestamp_order", f"[Shot {shot_index}] cut time must be strictly increasing.")
        if value <= 0 or value >= duration + 0.0005:
            result.error(
                "timestamp_range",
                f"[Shot {shot_index}] cut time {value:.3f}s must fall strictly inside {duration:.2f}s.",
            )
        previous = value
    return max(numbers) if numbers else 0


def _validate_dialogue_tags(text: str, result: ValidationResult) -> None:
    if text.count("<d>") != text.count("</d>"):
        result.error("dialogue_balance", "Every <d> dialogue tag must have a matching </d> tag.")
    for match in re.finditer(r"<d>(.*?)</d>", text, re.DOTALL):
        if not re.match(r"\[[^\]\n]+\]\s+\S", match.group(1).strip()):
            result.error("dialogue_language", "Each <d> block must begin with a [Language] tag and content.")


def _validate_alignment(text: str, code: str, duration: float, final_shot: int, result: ValidationResult) -> None:
    first_line = text.splitlines()[0].strip() if text.splitlines() else ""
    duration_text = f"{duration:.2f}"
    if code == "T2VA":
        if not text.startswith("integrated_multimodal_description:"):
            result.error("t2va_start", "T2VA must begin directly with integrated_multimodal_description:.")
        return
    if code == "I2VA":
        expected = (
            "For the target video, at 0.00 seconds into the target video, "
            "<Picture 1> (from [Shot 1]) is fully referenced."
        )
    elif code == "FL2VA":
        expected = (
            "How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with "
            f"the 0.00-second mark of the target video; Picture 2 (from Shot {final_shot}) aligns with the "
            f"{duration_text}-second mark of the target video."
        )
    else:
        expected = (
            "How the reference pictures align with the target video — "
            f"<Picture 1> (from [Shot {final_shot}]) aligns with the {duration_text}-second mark of the target video."
        )
    if first_line != expected:
        result.error("alignment_instruction", f"The first line must be exactly: {expected}")
    if "\n\n" not in text[: len(first_line) + 3]:
        result.error("alignment_blank_line", "The alignment instruction must be followed by one blank line.")


def _validate_base(text: str, code: str, duration: float, result: ValidationResult) -> None:
    sections = _extract_sections(text, BASE_FIELDS, result)
    body = sections.get("integrated_multimodal_description", "")
    final_shot = _validate_shots(body, duration, result)
    _validate_alignment(text, code, duration, final_shot or 1, result)
    _validate_dialogue_tags(text, result)


def _validate_summary(summary: str, result: ValidationResult) -> None:
    match = re.match(r"^\[([^\]]+)\]\s+\S", summary)
    if not match:
        result.error("summary_prefix", "summary must begin with a square-bracketed task-type prefix.")
        return
    values = [value.strip() for value in match.group(1).split("+")]
    invalid = [value for value in values if value not in SUMMARY_TYPES]
    if invalid:
        result.error("summary_task_type", f"Unknown summary task type(s): {', '.join(invalid)}.")
    if len(values) != len(set(values)):
        result.error("summary_duplicate_type", "summary must not repeat a task type.")


def _validate_retention(section: str, result: ValidationResult) -> None:
    entries = [line.strip() for line in section.splitlines() if line.strip().startswith("<")]
    if not entries:
        result.error("retention_entries", "retention_analysis must contain one reference-label entry per line.")
        return
    for line in entries:
        label = re.match(r"^<(Subject|Picture|Video|Audio)\s+\d+>", line)
        marker = re.search(r":\s*([a-z_]+)\s+-\s+\S", line)
        if not label or not marker:
            result.error("retention_format", f"Invalid retention entry: {line}")
            continue
        allowed = AUDIO_RETENTION_MARKERS if label.group(1) == "Audio" else VISIBLE_RETENTION_MARKERS
        if marker.group(1) not in allowed:
            result.error(
                "retention_marker",
                f"Marker {marker.group(1)} is invalid for <{label.group(1)} N> entries.",
            )


def _reference_labels(text: str) -> set[str]:
    return set(re.findall(r"<(?:Subject|Picture|Video|Audio)\s+\d+>", text))


def _validate_full_reference(text: str, duration: float, result: ValidationResult) -> None:
    if not text.startswith("subject_definitions:"):
        result.error("full_reference_start", "Full-reference output must begin with subject_definitions:.")
    sections = _extract_sections(text, FULL_REFERENCE_FIELDS, result)
    _validate_summary(sections.get("summary", ""), result)
    _validate_retention(sections.get("retention_analysis", ""), result)

    definitions = _reference_labels(sections.get("subject_definitions", ""))
    used = _reference_labels("\n".join(value for key, value in sections.items() if key != "subject_definitions"))
    undefined = sorted(used - definitions)
    if undefined:
        result.error(
            "undefined_reference", f"Reference labels used without a subject_definitions entry: {', '.join(undefined)}."
        )

    description = sections.get("detailed_description", "")
    _validate_shots(description, duration, result)
    _validate_dialogue_tags(description, result)
    word_count = len(re.findall(r"\b[A-Za-z]+(?:[-'][A-Za-z]+)*\b", description))
    if word_count and not 350 <= word_count <= 500:
        result.warning(
            "description_length",
            f"detailed_description contains about {word_count} English words; generation tasks normally target 350–500.",
        )


def validate_prompt(text: str, mode: str, duration: float) -> ValidationResult:
    result = ValidationResult()
    if not text.strip():
        result.error("empty_response", "The model response is empty.")
        return result
    code = mode_code(mode)
    if code == "FULL_REFERENCE":
        _validate_full_reference(text, duration, result)
    else:
        _validate_base(text, code, duration, result)
    return result
