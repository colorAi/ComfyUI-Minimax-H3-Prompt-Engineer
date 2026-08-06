# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Persistent local storage for AI-provider connection settings."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).with_name("provider_config.json")
CONFIG_VERSION = 1
MAX_FIELD_LENGTH = 16_384

PROVIDER_FIELDS = {
    "RunningHub": frozenset({"api_key", "site", "model"}),
    "OpenAI": frozenset({"api_key", "base_url", "model"}),
    "Local OpenAI-compatible": frozenset({"api_key", "base_url", "model"}),
}

_LOCK = threading.RLock()


def _normalize_provider(provider: str, values: Any) -> dict[str, str]:
    allowed = PROVIDER_FIELDS.get(provider)
    if allowed is None:
        raise ValueError(f"Unsupported persistent provider: {provider}")
    if not isinstance(values, dict):
        raise TypeError("Provider config must be a JSON object")

    normalized: dict[str, str] = {}
    for field in allowed:
        value = values.get(field)
        if value is None:
            continue
        if not isinstance(value, str):
            raise TypeError(f"Provider field {field} must be a string")
        if len(value) > MAX_FIELD_LENGTH:
            raise ValueError(f"Provider field {field} exceeds {MAX_FIELD_LENGTH} characters")
        normalized[field] = value
    return normalized


def _load_unlocked() -> dict[str, dict[str, str]]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}

    raw_providers = payload.get("providers", {})
    if not isinstance(raw_providers, dict):
        return {}
    providers: dict[str, dict[str, str]] = {}
    for provider, values in raw_providers.items():
        try:
            providers[provider] = _normalize_provider(provider, values)
        except (TypeError, ValueError):
            continue
    return providers


def load_provider_configs() -> dict[str, dict[str, str]]:
    """Load all supported provider settings without exposing unknown fields."""
    with _LOCK:
        return _load_unlocked()


def save_provider_config(provider: str, values: Any) -> dict[str, str]:
    """Atomically update one provider and keep the config file private where supported."""
    normalized = _normalize_provider(provider, values)
    with _LOCK:
        providers = _load_unlocked()
        providers[provider] = normalized
        payload = {"version": CONFIG_VERSION, "providers": providers}
        temporary_path = CONFIG_PATH.with_suffix(CONFIG_PATH.suffix + ".tmp")
        descriptor = os.open(temporary_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, CONFIG_PATH)
            try:
                os.chmod(CONFIG_PATH, 0o600)
            except OSError:
                pass
        finally:
            if temporary_path.exists():
                temporary_path.unlink()
    return normalized
