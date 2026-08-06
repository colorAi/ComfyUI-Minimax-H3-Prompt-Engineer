# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Unified prompt engineering + official MiniMax H3 conditioning node."""

from __future__ import annotations

import json
from typing import Any

from comfy_api.latest import io
from comfy_extras import nodes_minimax_h3 as comfy_h3

try:
    from .asset_refs import AssetBundle, keyframe_bundle
    from .openai_compatible_client import (
        LOCAL_DEFAULT_BASE_URL,
        LOCAL_DEFAULT_MODEL,
        OPENAI_BASE_URL,
        OPENAI_DEFAULT_MODEL,
        CompatibleAPIError,
        OpenAICompatibleClient,
    )
    from .presets import CreativePresets
    from .prompt_builder import (
        MODE_FL2VA,
        MODE_FULL_REFERENCE,
        MODE_I2VA,
        MODE_L2VA,
        MODE_T2VA,
        TASK_MODES,
        ReferenceImage,
        build_messages,
        build_repair_messages,
        mode_code,
    )
    from .runninghub_client import (
        DEFAULT_MODEL,
        RUNNINGHUB_SITES,
        SITE_GLOBAL,
        RunningHubClient,
        RunningHubError,
    )
    from .templates import DEFAULT_TEMPLATE, PROMPT_TEMPLATES
    from .validators import clean_model_response, validate_prompt
except ImportError:  # Allows direct loading when ComfyUI imports custom modules unusually.
    from asset_refs import AssetBundle, keyframe_bundle
    from openai_compatible_client import (
        LOCAL_DEFAULT_BASE_URL,
        LOCAL_DEFAULT_MODEL,
        OPENAI_BASE_URL,
        OPENAI_DEFAULT_MODEL,
        CompatibleAPIError,
        OpenAICompatibleClient,
    )
    from presets import CreativePresets
    from prompt_builder import (
        MODE_FL2VA,
        MODE_FULL_REFERENCE,
        MODE_I2VA,
        MODE_L2VA,
        MODE_T2VA,
        TASK_MODES,
        ReferenceImage,
        build_messages,
        build_repair_messages,
        mode_code,
    )
    from runninghub_client import (
        DEFAULT_MODEL,
        RUNNINGHUB_SITES,
        SITE_GLOBAL,
        RunningHubClient,
        RunningHubError,
    )
    from templates import DEFAULT_TEMPLATE, PROMPT_TEMPLATES
    from validators import clean_model_response, validate_prompt


MODE_AUTO = "Auto · Infer from connected assets"

PROVIDER_RUNNINGHUB = "RunningHub"
PROVIDER_OPENAI = "OpenAI"
PROVIDER_LOCAL = "Local OpenAI-compatible"
PROVIDER_DIRECT = "Direct · Prompt already formatted"


class MinimaxH3PromptStudio(io.ComfyNode):
    """Generate the prompt and H3 conditioning from one authoritative set of material inputs."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        max_resolution = comfy_h3.nodes.MAX_RESOLUTION
        return io.Schema(
            node_id="MinimaxH3PromptStudio",
            display_name="MiniMax H3 Prompt Studio + Generate",
            category="MiniMax H3/Prompt Engineer",
            description=(
                "One-node prompt engineering and official MiniMax H3 conditioning. Connect each image, video, "
                "or audio once; use @图像1, @视频1, @视频音频1, and @音频1 in the request."
            ),
            is_output_node=True,
            inputs=[
                io.Clip.Input("clip"),
                io.Vae.Input("vae"),
                io.DynamicCombo.Input(
                    "ai_provider",
                    options=[
                        io.DynamicCombo.Option(
                            PROVIDER_RUNNINGHUB,
                            [
                                io.String.Input(
                                    "api_key",
                                    default="",
                                    placeholder="RunningHub Enterprise-Shared API Key",
                                ),
                                io.Combo.Input("site", options=RUNNINGHUB_SITES, default=SITE_GLOBAL),
                                io.String.Input("model", default=DEFAULT_MODEL),
                            ],
                        ),
                        io.DynamicCombo.Option(
                            PROVIDER_OPENAI,
                            [
                                io.String.Input("api_key", default="", placeholder="OpenAI API Key"),
                                io.String.Input("base_url", default=OPENAI_BASE_URL),
                                io.String.Input("model", default=OPENAI_DEFAULT_MODEL),
                            ],
                        ),
                        io.DynamicCombo.Option(
                            PROVIDER_LOCAL,
                            [
                                io.String.Input("base_url", default=LOCAL_DEFAULT_BASE_URL),
                                io.String.Input("model", default=LOCAL_DEFAULT_MODEL),
                                io.String.Input(
                                    "api_key",
                                    default="",
                                    placeholder="Optional; leave empty unless the local server requires it",
                                ),
                            ],
                        ),
                        io.DynamicCombo.Option(PROVIDER_DIRECT, []),
                    ],
                    tooltip="Only the settings needed by the selected provider are shown.",
                ),
                io.Combo.Input("prompt_template", options=PROMPT_TEMPLATES, default=DEFAULT_TEMPLATE),
                io.Combo.Input("task_mode", options=[MODE_AUTO, *TASK_MODES], default=MODE_AUTO),
                io.String.Input(
                    "user_request",
                    multiline=True,
                    dynamic_prompts=False,
                    placeholder=(
                        "例如：@图像1 里的女孩登上 @视频1 的列车；环境声参考 @音频1。"
                        " Direct 模式请粘贴完整 H3 提示词。"
                    ),
                ),
                io.Int.Input("width", default=1344, min=32, max=max_resolution, step=32),
                io.Int.Input("height", default=768, min=32, max=max_resolution, step=32),
                io.Int.Input(
                    "length",
                    default=124,
                    min=5,
                    max=3600,
                    step=17,
                    tooltip="Frame count at 24 fps; H3 snaps upward to its 17k+5 frame grid.",
                ),
                io.Combo.Input(
                    "ref_image_size",
                    options=["match", "max"],
                    default="match",
                    tooltip="Matches the official MiniMax H3 Reference to Video node.",
                ),
                io.String.Input(
                    "reference_context",
                    multiline=True,
                    dynamic_prompts=False,
                    default="",
                    placeholder="Optional exact roles, dialogue, lyrics, visible text, or audio content notes.",
                    advanced=True,
                ),
                io.Vae.Input("audio_vae", optional=True, advanced=True),
                io.Image.Input("first_frame", optional=True),
                io.Image.Input("last_frame", optional=True),
                io.Autogrow.Input(
                    "ref_images",
                    optional=True,
                    template=io.Autogrow.TemplatePrefix(
                        input=io.Image.Input("ref_image", tooltip="Reference image"),
                        prefix="ref_image_",
                        min=0,
                        max=9,
                    ),
                ),
                io.Autogrow.Input(
                    "ref_videos",
                    optional=True,
                    template=io.Autogrow.TemplatePrefix(
                        input=io.Image.Input("ref_video", tooltip="Reference video frames at 24 fps"),
                        prefix="ref_video_",
                        min=0,
                        max=3,
                    ),
                ),
                io.Autogrow.Input(
                    "ref_video_audios",
                    optional=True,
                    template=io.Autogrow.TemplatePrefix(
                        input=io.Audio.Input("ref_video_audio", tooltip="Soundtrack of the same-numbered video"),
                        prefix="ref_video_audio_",
                        min=0,
                        max=3,
                    ),
                ),
                io.Autogrow.Input(
                    "ref_audios",
                    optional=True,
                    template=io.Autogrow.TemplatePrefix(
                        input=io.Audio.Input("ref_audio", tooltip="Standalone reference audio"),
                        prefix="ref_audio_",
                        min=0,
                        max=3,
                    ),
                ),
                io.Custom("H3_CREATIVE_PRESET").Input("creative_presets", optional=True, advanced=True),
                io.Float.Input("temperature", default=0.2, min=0.0, max=2.0, step=0.05, advanced=True),
                io.Float.Input("top_p", default=0.9, min=0.0, max=1.0, step=0.05, advanced=True),
                io.Int.Input("max_tokens", default=4096, min=512, max=32768, step=256, advanced=True),
                io.Combo.Input(
                    "reasoning_effort",
                    options=["none", "minimal", "low", "medium", "high", "xhigh", "max"],
                    default="none",
                    advanced=True,
                ),
                io.Int.Input("timeout_seconds", default=120, min=10, max=600, step=10, advanced=True),
                io.Int.Input("image_max_side", default=1024, min=512, max=4096, step=128, advanced=True),
                io.Boolean.Input("auto_repair", default=True, advanced=True),
                io.Boolean.Input("strict_validation", default=True, advanced=True),
            ],
            outputs=[
                io.Conditioning.Output("positive"),
                io.Latent.Output("latent"),
                io.String.Output("formatted_prompt"),
                io.String.Output("validation_report"),
                io.String.Output("raw_response"),
                io.String.Output("usage_json"),
            ],
        )

    @staticmethod
    def _resolve_mode(
        requested_mode: str,
        *,
        bundle: AssetBundle,
        first_frame: Any,
        last_frame: Any,
    ) -> str:
        has_first = first_frame is not None
        has_last = last_frame is not None
        if requested_mode == MODE_AUTO:
            if bundle.has_references:
                if has_first or has_last:
                    raise ValueError(
                        "first_frame/last_frame cannot be mixed with Full Reference assets. "
                        "Use either the H3 keyframe path or the H3 reference path."
                    )
                return MODE_FULL_REFERENCE
            if has_first and has_last:
                return MODE_FL2VA
            if has_first:
                return MODE_I2VA
            if has_last:
                return MODE_L2VA
            return MODE_T2VA

        code = mode_code(requested_mode)
        if code == "FULL_REFERENCE":
            if has_first or has_last:
                raise ValueError("FULL_REFERENCE uses ref_images/ref_videos/ref_audios, not first_frame/last_frame")
            if not bundle.has_references:
                raise ValueError("FULL_REFERENCE requires at least one connected reference material")
            return MODE_FULL_REFERENCE
        if bundle.has_references:
            raise ValueError(f"{code} cannot use Full Reference inputs; choose FULL_REFERENCE or Auto")
        requirements = {
            "T2VA": (False, False),
            "I2VA": (True, False),
            "FL2VA": (True, True),
            "L2VA": (False, True),
        }
        expected_first, expected_last = requirements[code]
        if has_first != expected_first or has_last != expected_last:
            needed = {
                "T2VA": "no keyframes",
                "I2VA": "first_frame only",
                "FL2VA": "both first_frame and last_frame",
                "L2VA": "last_frame only",
            }[code]
            raise ValueError(f"{code} requires {needed}")
        return requested_mode

    @staticmethod
    def _provider_client(
        provider_config: dict[str, Any],
        *,
        timeout_seconds: int,
    ) -> tuple[str, Any, str, dict[str, Any]]:
        provider = str(provider_config.get("ai_provider", ""))
        api_key = str(provider_config.get("api_key", ""))
        model_value = str(provider_config.get("model", ""))
        if provider == PROVIDER_RUNNINGHUB:
            if not api_key.strip():
                raise ValueError("RunningHub api_key cannot be empty")
            site = str(provider_config.get("site", SITE_GLOBAL))
            base_url = RunningHubClient.base_url_for_site(site)
            model = model_value.strip() or DEFAULT_MODEL
            client = RunningHubClient(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout_seconds,
            )
            return provider, client, model, {"site": site, "endpoint": f"{base_url}/chat/completions"}
        if provider == PROVIDER_OPENAI:
            model = model_value.strip() or OPENAI_DEFAULT_MODEL
            client = OpenAICompatibleClient(
                provider=PROVIDER_OPENAI,
                base_url=str(provider_config.get("base_url", OPENAI_BASE_URL)),
                api_key=api_key,
                timeout=timeout_seconds,
                require_api_key=True,
                token_field="max_completion_tokens",
                supports_reasoning_effort=True,
            )
            return provider, client, model, {"endpoint": f"{client.base_url}/chat/completions"}
        if provider == PROVIDER_LOCAL:
            model = model_value.strip()
            client = OpenAICompatibleClient(
                provider=PROVIDER_LOCAL,
                base_url=str(provider_config.get("base_url", LOCAL_DEFAULT_BASE_URL)),
                api_key=api_key,
                timeout=timeout_seconds,
                token_field="max_tokens",
                supports_reasoning_effort=False,
            )
            return provider, client, model, {"endpoint": f"{client.base_url}/chat/completions"}
        if provider == PROVIDER_DIRECT:
            return provider, None, "direct", {"endpoint": None}
        raise ValueError(f"Unsupported ai_provider: {provider}")

    @staticmethod
    def _usage_entry(result: Any, phase: str) -> dict[str, Any]:
        return {
            "phase": phase,
            "model": result.model,
            "request_id": result.request_id,
            "usage": result.usage,
        }

    @classmethod
    def _engineer_prompt(
        cls,
        *,
        provider: str,
        client: Any,
        model: str,
        provider_metadata: dict[str, Any],
        alias_plan: AssetBundle,
        mode: str,
        prompt_template: str,
        user_request: str,
        duration: float,
        reference_context: str,
        presets: Any,
        vision_references: list[ReferenceImage],
        image_max_side: int,
        temperature: float,
        top_p: float,
        max_tokens: int,
        reasoning_effort: str,
        auto_repair: bool,
        strict_validation: bool,
    ) -> tuple[str, str, str, str]:
        calls: list[dict[str, Any]] = []
        raw_outputs: dict[str, str] = {}

        if provider == PROVIDER_DIRECT:
            formatted = alias_plan.resolve_text(clean_model_response(user_request, mode))
            validation = validate_prompt(formatted, mode, duration)
        else:
            messages = build_messages(
                mode=mode,
                user_request=user_request,
                duration=duration,
                reference_context=reference_context,
                presets=CreativePresets.from_value(presets),
                reference_images=vision_references,
                image_max_side=image_max_side,
                template=prompt_template,
            )
            try:
                initial = client.chat(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    reasoning_effort=reasoning_effort,
                )
                calls.append(cls._usage_entry(initial, "initial"))
                raw_outputs["initial_response"] = initial.content
                formatted = alias_plan.resolve_text(clean_model_response(initial.content, mode))
                validation = validate_prompt(formatted, mode, duration)

                if not validation.is_valid and auto_repair:
                    repair = client.chat(
                        model=model,
                        messages=build_repair_messages(
                            mode=mode,
                            duration=duration,
                            previous_response=formatted,
                            validation_report=validation.report(),
                            template=prompt_template,
                        ),
                        max_tokens=max_tokens,
                        temperature=0.0,
                        top_p=1.0,
                        reasoning_effort="none",
                    )
                    calls.append(cls._usage_entry(repair, "repair"))
                    raw_outputs["repair_response"] = repair.content
                    formatted = alias_plan.resolve_text(clean_model_response(repair.content, mode))
                    validation = validate_prompt(formatted, mode, duration)
            except (RunningHubError, CompatibleAPIError) as exc:
                raise RuntimeError(exc.user_message()) from exc

        report = validation.report()
        if strict_validation and not validation.is_valid:
            raise ValueError(f"{provider} produced a prompt that fails strict H3 validation:\n{report}")
        usage = {
            "provider": provider,
            "selected_model": model,
            "task_mode": mode_code(mode),
            "effective_duration_seconds": duration,
            **provider_metadata,
            "calls": calls,
        }
        return (
            formatted,
            report,
            json.dumps(raw_outputs, ensure_ascii=False, indent=2),
            json.dumps(usage, ensure_ascii=False, indent=2),
        )

    @classmethod
    def execute(
        cls,
        clip: Any,
        vae: Any,
        ai_provider: dict[str, Any],
        prompt_template: str,
        task_mode: str,
        user_request: str,
        width: int,
        height: int,
        length: int,
        ref_image_size: str,
        reference_context: str,
        temperature: float,
        top_p: float,
        max_tokens: int,
        reasoning_effort: str,
        timeout_seconds: int,
        image_max_side: int,
        auto_repair: bool,
        strict_validation: bool,
        audio_vae: Any = None,
        first_frame: Any = None,
        last_frame: Any = None,
        ref_images: dict[str, Any] | None = None,
        ref_videos: dict[str, Any] | None = None,
        ref_video_audios: dict[str, Any] | None = None,
        ref_audios: dict[str, Any] | None = None,
        creative_presets: Any = None,
    ) -> io.NodeOutput:
        if not user_request.strip():
            raise ValueError("user_request cannot be empty")

        bundle = AssetBundle.from_autogrow(
            ref_images=ref_images,
            ref_videos=ref_videos,
            ref_video_audios=ref_video_audios,
            ref_audios=ref_audios,
        )
        mode = cls._resolve_mode(
            task_mode,
            bundle=bundle,
            first_frame=first_frame,
            last_frame=last_frame,
        )
        if bundle.has_audio and audio_vae is None:
            raise ValueError("audio_vae is required when reference audio or a reference-video soundtrack is connected")

        if mode == MODE_FULL_REFERENCE:
            alias_plan = bundle
            vision_references = bundle.vision_references()
        else:
            alias_plan = keyframe_bundle(first_frame=first_frame, last_frame=last_frame)
            vision_references = []
            if first_frame is not None:
                vision_references.append(
                    ReferenceImage("<Picture 1>", "the exact first frame at 0.00 seconds", first_frame[:1])
                )
            if last_frame is not None:
                picture_number = 2 if first_frame is not None else 1
                vision_references.append(
                    ReferenceImage(
                        f"<Picture {picture_number}>",
                        "the exact final frame at the effective duration",
                        last_frame[:1],
                    )
                )

        resolved_request = alias_plan.resolve_text(user_request)
        combined_context = "\n\n".join(
            item for item in [alias_plan.context_text(), alias_plan.resolve_text(reference_context)] if item.strip()
        )
        frame_count, _, _ = comfy_h3.temporal_shape(length)
        duration = round(frame_count / comfy_h3.FPS, 2)

        provider, client, model, provider_metadata = cls._provider_client(
            ai_provider,
            timeout_seconds=timeout_seconds,
        )
        formatted, report, raw_response, usage_json = cls._engineer_prompt(
            provider=provider,
            client=client,
            model=model,
            provider_metadata=provider_metadata,
            alias_plan=alias_plan,
            mode=mode,
            prompt_template=prompt_template,
            user_request=resolved_request,
            duration=duration,
            reference_context=combined_context,
            presets=creative_presets,
            vision_references=vision_references,
            image_max_side=image_max_side,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            auto_repair=auto_repair,
            strict_validation=strict_validation,
        )
        if mode == MODE_FULL_REFERENCE:
            generated = comfy_h3.MiniMaxH3ReferenceToVideo.execute(
                clip,
                vae,
                audio_vae,
                formatted,
                width,
                height,
                length,
                ref_image_size,
                bundle.ref_images,
                bundle.ref_videos,
                bundle.ref_video_audios,
                bundle.ref_audios,
            )
        else:
            generated = comfy_h3.MiniMaxH3ImageToVideo.execute(
                clip,
                vae,
                formatted,
                width,
                height,
                length,
                first_frame,
                last_frame,
            )
        positive, latent = generated.result
        return io.NodeOutput(positive, latent, formatted, report, raw_response, usage_json)
