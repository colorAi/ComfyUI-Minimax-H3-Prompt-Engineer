# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Dependency-light Chat Completions client for OpenAI and local compatible servers."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

try:
    import certifi

    _TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # certifi ships with standard ComfyUI builds, but retain a stdlib fallback.
    _TLS_CONTEXT = ssl.create_default_context()


OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_DEFAULT_MODEL = "gpt-5.6-sol"
LOCAL_DEFAULT_BASE_URL = "http://127.0.0.1:11434/v1"
LOCAL_DEFAULT_MODEL = "qwen3-vl:8b"


class CompatibleAPIError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        provider: str,
        status: int | None = None,
        code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status = status
        self.code = code
        self.request_id = request_id

    def user_message(self) -> str:
        parts = [f"{self.provider}: {self}"]
        if self.status is not None:
            parts.append(f"HTTP {self.status}")
        if self.code:
            parts.append(f"code={self.code}")
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        return " | ".join(parts)


@dataclass(slots=True)
class CompatibleChatResult:
    content: str
    usage: dict[str, Any]
    model: str
    request_id: str | None
    raw: dict[str, Any]


class OpenAICompatibleClient:
    """Call an OpenAI-style ``/chat/completions`` endpoint without requiring an SDK."""

    def __init__(
        self,
        *,
        provider: str,
        base_url: str,
        api_key: str = "",
        timeout: float = 120.0,
        require_api_key: bool = False,
        token_field: str = "max_tokens",
        supports_reasoning_effort: bool = False,
    ) -> None:
        normalized_url = base_url.strip().rstrip("/")
        if not normalized_url.startswith(("http://", "https://")):
            raise ValueError(f"{provider} base_url must begin with http:// or https://")
        if require_api_key and not api_key.strip():
            raise ValueError(f"{provider} api_key cannot be empty")
        if token_field not in {"max_tokens", "max_completion_tokens"}:
            raise ValueError(f"Unsupported completion token field: {token_field}")
        self.provider = provider
        self.base_url = normalized_url
        self.api_key = api_key.strip()
        self.timeout = max(1.0, float(timeout))
        self.token_field = token_field
        self.supports_reasoning_effort = supports_reasoning_effort

    @staticmethod
    def _request_id(headers: Any) -> str | None:
        if headers is None:
            return None
        return headers.get("x-request-id") or headers.get("request-id")

    def _decode_json(self, data: bytes) -> dict[str, Any]:
        try:
            decoded = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CompatibleAPIError(
                f"server returned invalid JSON: {exc}", provider=self.provider
            ) from exc
        if not isinstance(decoded, dict):
            raise CompatibleAPIError("server returned an unexpected JSON value", provider=self.provider)
        return decoded

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
    ) -> CompatibleChatResult:
        if not model.strip():
            raise ValueError(f"{self.provider} model cannot be empty")
        payload: dict[str, Any] = {
            "model": model.strip(),
            "messages": list(messages),
            self.token_field: int(max_tokens),
            "temperature": float(temperature),
            "top_p": float(top_p),
            "stream": False,
        }
        if self.supports_reasoning_effort and reasoning_effort and reasoning_effort != "default":
            payload["reasoning_effort"] = reasoning_effort

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-Minimax-H3-Prompt-Engineer/0.4.2",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=_TLS_CONTEXT) as response:
                decoded = self._decode_json(response.read())
                request_id = self._request_id(response.headers)
        except urllib.error.HTTPError as exc:
            body = exc.read()
            request_id = self._request_id(exc.headers)
            message = f"request failed with HTTP {exc.code}"
            code = None
            if body:
                try:
                    decoded_error = self._decode_json(body)
                    error = decoded_error.get("error", decoded_error)
                    if isinstance(error, dict):
                        message = str(error.get("message") or message)
                        code = error.get("code")
                    elif error:
                        message = str(error)
                except CompatibleAPIError:
                    pass
            raise CompatibleAPIError(
                message,
                provider=self.provider,
                status=exc.code,
                code=str(code) if code else None,
                request_id=request_id,
            ) from exc
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            raise CompatibleAPIError(
                f"could not reach {self.base_url}: {reason}", provider=self.provider
            ) from exc
        except TimeoutError as exc:
            raise CompatibleAPIError(
                f"request timed out after {self.timeout:g} seconds", provider=self.provider
            ) from exc

        choices = decoded.get("choices")
        if not isinstance(choices, list) or not choices:
            raise CompatibleAPIError(
                "server returned no completion choices", provider=self.provider, request_id=request_id
            )
        first = choices[0]
        message = first.get("message") if isinstance(first, dict) else None
        content = self._extract_content(message)
        if not content.strip():
            raise CompatibleAPIError(
                "server returned an empty assistant response", provider=self.provider, request_id=request_id
            )
        usage = decoded.get("usage") if isinstance(decoded.get("usage"), dict) else {}
        return CompatibleChatResult(
            content=content,
            usage=usage,
            model=str(decoded.get("model") or model),
            request_id=request_id,
            raw=decoded,
        )
