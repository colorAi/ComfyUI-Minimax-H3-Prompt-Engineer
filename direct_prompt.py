# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Direct prompt modes that do not call an LLM provider."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

try:
    from .validators import clean_model_response, validate_prompt
except ImportError:  # Allows direct imports in local tests.
    from validators import clean_model_response, validate_prompt


PROVIDER_DIRECT_RAW = "Direct · Use prompt as-is"
PROVIDER_DIRECT_STRICT = "Direct · Prompt already formatted"
DIRECT_PROVIDERS = frozenset({PROVIDER_DIRECT_RAW, PROVIDER_DIRECT_STRICT})


@dataclass(frozen=True, slots=True)
class DirectPromptResult:
    formatted: str
    validation_report: str
    is_valid: bool
    validation_skipped: bool


def prepare_direct_prompt(
    *,
    provider: str,
    user_request: str,
    resolve_text: Callable[[str], str],
    mode: str,
    duration: float,
    request_level: str,
) -> DirectPromptResult:
    """Resolve asset aliases, optionally enforcing the complete H3 document schema."""
    if provider not in DIRECT_PROVIDERS:
        raise ValueError(f"Unsupported Direct provider: {provider}")

    if provider == PROVIDER_DIRECT_RAW:
        formatted = resolve_text(user_request.strip())
        return DirectPromptResult(
            formatted=formatted,
            validation_report=(
                "SKIPPED — Direct pass-through mode resolved connected-asset aliases and intentionally bypassed "
                "the structured H3 document validator."
            ),
            is_valid=True,
            validation_skipped=True,
        )

    formatted = resolve_text(clean_model_response(user_request, mode))
    validation = validate_prompt(formatted, mode, duration, request_level=request_level)
    return DirectPromptResult(
        formatted=formatted,
        validation_report=validation.report(),
        is_valid=validation.is_valid,
        validation_skipped=False,
    )
