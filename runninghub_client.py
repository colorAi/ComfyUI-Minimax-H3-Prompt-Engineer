# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Small dependency-free client for RunningHub's OpenAI-compatible LLM API."""

from __future__ import annotations

import json
import ssl
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, ClassVar

try:
    import certifi

    _TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # certifi ships with standard ComfyUI builds, but retain a stdlib fallback.
    _TLS_CONTEXT = ssl.create_default_context()


SITE_GLOBAL = "RunningHub Global (.ai)"
SITE_CHINA = "RunningHub China (.cn)"
RUNNINGHUB_SITES = [SITE_GLOBAL, SITE_CHINA]
SITE_BASE_URLS = {
    SITE_GLOBAL: "https://llm.runninghub.ai/v1",
    SITE_CHINA: "https://llm.runninghub.cn/v1",
}
DEFAULT_BASE_URL = SITE_BASE_URLS[SITE_GLOBAL]
DEFAULT_MODEL = "qwen/qwen3.6-plus"
FALLBACK_MODELS_BY_SITE = {
    SITE_GLOBAL: [
        DEFAULT_MODEL,
        "google/gemini-3.5-flash-lite",
        "minimax/minimax-m2.7",
        "bytedance/doubao-seed-2.0-mini",
        "glm-5.2",
    ],
    SITE_CHINA: [
        DEFAULT_MODEL,
        "qwen/qwen3.7-plus",
        "glm-5v-turbo",
        "minimax/minimax-m2.7",
        "bytedance/doubao-seed-2.0-mini",
        "glm-5.2",
    ],
}


class RunningHubError(RuntimeError):
    """Error returned by RunningHub or raised while reaching its API."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.request_id = request_id

    def user_message(self) -> str:
        parts = [str(self)]
        if self.status is not None:
            parts.append(f"HTTP {self.status}")
        if self.code:
            parts.append(f"code={self.code}")
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        return " | ".join(parts)


@dataclass(slots=True)
class ModelInfo:
    id: str
    context_length: int | None
    capabilities: dict[str, Any]
    pricing: dict[str, Any]
    raw: dict[str, Any]

    @property
    def supports_vision(self) -> bool | None:
        value = self.capabilities.get("vision")
        return value if isinstance(value, bool) else None


@dataclass(slots=True)
class ChatResult:
    content: str
    usage: dict[str, Any]
    model: str
    request_id: str | None
    raw: dict[str, Any]


class RunningHubClient:
    """OpenAI Chat Completions client with a short-lived public model cache."""

    _models_lock = threading.Lock()
    _models_cache: ClassVar[dict[str, tuple[float, list[ModelInfo]]]] = {}

    def __init__(
        self,
        api_key: str = "",
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = max(1.0, float(timeout))

    @staticmethod
    def base_url_for_site(site: str) -> str:
        try:
            return SITE_BASE_URLS[site]
        except KeyError as exc:
            raise ValueError(f"Unsupported RunningHub site: {site}") from exc

    @staticmethod
    def site_for_base_url(base_url: str) -> str | None:
        normalized = base_url.rstrip("/")
        return next((site for site, url in SITE_BASE_URLS.items() if url == normalized), None)

    @staticmethod
    def _request_id(headers: Any) -> str | None:
        if headers is None:
            return None
        return headers.get("x-llm-request-id") or headers.get("x-request-id")

    @staticmethod
    def _decode_json(data: bytes, *, context: str) -> dict[str, Any]:
        try:
            decoded = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RunningHubError(f"RunningHub returned invalid JSON for {context}: {exc}") from exc
        if not isinstance(decoded, dict):
            raise RunningHubError(f"RunningHub returned an unexpected JSON value for {context}")
        return decoded

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        require_key: bool = False,
        timeout: float | None = None,
    ) -> tuple[dict[str, Any], str | None]:
        if require_key and not self.api_key:
            raise RunningHubError(
                "RunningHub API Key is required. LLM calls require an Enterprise-Shared API Key.",
                code="auth_apikey_missing",
            )

        headers = {
            "Accept": "application/json",
            "User-Agent": "ComfyUI-Minimax-H3-Prompt-Engineer/0.4.0",
        }
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = urllib.request.Request(
            f"{self.base_url}/{path.lstrip('/')}",
            data=data,
            headers=headers,
            method=method.upper(),
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=timeout or self.timeout,
                context=_TLS_CONTEXT,
            ) as response:
                body = response.read()
                request_id = self._request_id(response.headers)
                return self._decode_json(body, context=path), request_id
        except urllib.error.HTTPError as exc:
            body = exc.read()
            request_id = self._request_id(exc.headers)
            message = f"RunningHub request failed with HTTP {exc.code}"
            code = None
            if body:
                try:
                    decoded = self._decode_json(body, context=path)
                    error = decoded.get("error", decoded)
                    if isinstance(error, dict):
                        message = str(error.get("message") or message)
                        code = error.get("code")
                    elif error:
                        message = str(error)
                except RunningHubError:
                    pass
            raise RunningHubError(
                message,
                status=exc.code,
                code=str(code) if code else None,
                request_id=request_id,
            ) from exc
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            raise RunningHubError(f"Could not reach RunningHub: {reason}") from exc
        except TimeoutError as exc:
            raise RunningHubError(f"RunningHub request timed out after {timeout or self.timeout:g} seconds") from exc

    @classmethod
    def list_models(
        cls,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 5.0,
        max_age: float = 300.0,
        force_refresh: bool = False,
    ) -> list[ModelInfo]:
        now = time.monotonic()
        with cls._models_lock:
            cached = cls._models_cache.get(base_url.rstrip("/"))
            if not force_refresh and cached and now - cached[0] <= max_age:
                return list(cached[1])

        client = cls(base_url=base_url, timeout=timeout)
        response, _ = client._request_json("GET", "models", timeout=timeout)
        raw_models = response.get("data")
        if not isinstance(raw_models, list):
            raise RunningHubError("RunningHub /models response does not contain a data list")

        models: list[ModelInfo] = []
        for raw in raw_models:
            if not isinstance(raw, dict) or not isinstance(raw.get("id"), str):
                continue
            models.append(
                ModelInfo(
                    id=raw["id"],
                    context_length=raw.get("context_length") if isinstance(raw.get("context_length"), int) else None,
                    capabilities=raw.get("capabilities") if isinstance(raw.get("capabilities"), dict) else {},
                    pricing=raw.get("pricing") if isinstance(raw.get("pricing"), dict) else {},
                    raw=raw,
                )
            )
        if not models:
            raise RunningHubError("RunningHub /models response does not contain any usable model entries")
        models.sort(key=lambda item: item.id.lower())
        with cls._models_lock:
            cls._models_cache[base_url.rstrip("/")] = (time.monotonic(), models)
        return list(models)

    @classmethod
    def model_ids(cls, *, base_url: str = DEFAULT_BASE_URL, timeout: float = 3.0) -> list[str]:
        try:
            ids = [item.id for item in cls.list_models(base_url=base_url, timeout=timeout)]
        except RunningHubError:
            site = cls.site_for_base_url(base_url) or SITE_GLOBAL
            ids = list(FALLBACK_MODELS_BY_SITE[site])
        ordered = [DEFAULT_MODEL]
        ordered.extend(item for item in ids if item != DEFAULT_MODEL)
        return ordered

    @classmethod
    def find_model(
        cls,
        model_id: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 3.0,
    ) -> ModelInfo | None:
        try:
            return next(
                (item for item in cls.list_models(base_url=base_url, timeout=timeout) if item.id == model_id),
                None,
            )
        except RunningHubError:
            return None

    @staticmethod
    def _extract_content(message: Any) -> str:
        if not isinstance(message, dict):
            return ""
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            chunks: list[str] = []
            for part in content:
                if isinstance(part, str):
                    chunks.append(part)
                elif isinstance(part, dict) and isinstance(part.get("text"), str):
                    chunks.append(part["text"])
            return "".join(chunks)
        return ""

    def chat(
        self,
        *,
        model: str,
        messages: Iterable[dict[str, Any]],
        max_tokens: int = 4096,
        temperature: float = 0.2,
        top_p: float = 0.9,
        reasoning_effort: str = "none",
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
    ) -> ChatResult:
        payload: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "top_p": float(top_p),
            "presence_penalty": float(presence_penalty),
            "frequency_penalty": float(frequency_penalty),
            "stream": False,
        }
        if reasoning_effort and reasoning_effort != "default":
            payload["reasoning_effort"] = reasoning_effort

        response, request_id = self._request_json(
            "POST",
            "chat/completions",
            payload=payload,
            require_key=True,
        )
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RunningHubError(
                "RunningHub returned no completion choices",
                request_id=request_id,
            )
        first = choices[0]
        message = first.get("message") if isinstance(first, dict) else None
        content = self._extract_content(message)
        if not content.strip():
            raise RunningHubError(
                "RunningHub returned an empty assistant response",
                request_id=request_id,
            )
        usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
        return ChatResult(
            content=content,
            usage=usage,
            model=str(response.get("model") or model),
            request_id=request_id,
            raw=response,
        )
