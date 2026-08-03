# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""ComfyUI nodes for MiniMax H3 prompt engineering through RunningHub."""

from __future__ import annotations

import json
from typing import Any

try:
    from .image_utils import split_image_batch
    from .presets import (
        CAMERA_ANGLES,
        CAMERA_MOTIONS,
        ENVIRONMENTS,
        LIGHTING,
        MOTION_AMPLITUDES,
        MOTION_SPEEDS,
        MUSIC,
        SHOT_SIZES,
        SHOT_STRUCTURES,
        SOUNDSCAPES,
        TIME_WEATHER,
        VISUAL_STYLES,
        CreativePresets,
    )
    from .prompt_builder import (
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
    from .validators import clean_model_response, validate_prompt
except ImportError:  # Allows importing the module outside a package during tests.
    from image_utils import split_image_batch
    from presets import (
        CAMERA_ANGLES,
        CAMERA_MOTIONS,
        ENVIRONMENTS,
        LIGHTING,
        MOTION_AMPLITUDES,
        MOTION_SPEEDS,
        MUSIC,
        SHOT_SIZES,
        SHOT_STRUCTURES,
        SOUNDSCAPES,
        TIME_WEATHER,
        VISUAL_STYLES,
        CreativePresets,
    )
    from prompt_builder import (
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
    from validators import clean_model_response, validate_prompt


NODE_CATEGORY = "MiniMax H3/Prompt Engineer"


class H3CreativePresetsNode:
    """Build a reusable creative-control object for the main prompt node."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "visual_style": (VISUAL_STYLES,),
                "environment": (ENVIRONMENTS,),
                "time_weather": (TIME_WEATHER,),
                "lighting": (LIGHTING,),
                "shot_size": (SHOT_SIZES,),
                "camera_angle": (CAMERA_ANGLES,),
                "camera_motion": (CAMERA_MOTIONS,),
                "motion_amplitude": (MOTION_AMPLITUDES,),
                "motion_speed": (MOTION_SPEEDS,),
                "shot_structure": (SHOT_STRUCTURES,),
                "soundscape": (SOUNDSCAPES,),
                "music": (MUSIC,),
                "custom_instructions": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "placeholder": "Optional custom lens, lighting, camera, sound, or continuity rules",
                    },
                ),
            }
        }

    RETURN_TYPES = ("H3_CREATIVE_PRESET",)
    RETURN_NAMES = ("creative_presets",)
    FUNCTION = "build"
    CATEGORY = NODE_CATEGORY

    def build(
        self,
        visual_style: str,
        environment: str,
        time_weather: str,
        lighting: str,
        shot_size: str,
        camera_angle: str,
        camera_motion: str,
        motion_amplitude: str,
        motion_speed: str,
        shot_structure: str,
        soundscape: str,
        music: str,
        custom_instructions: str,
    ) -> tuple[dict[str, Any]]:
        presets = CreativePresets(
            visual_style=visual_style,
            environment=environment,
            time_weather=time_weather,
            lighting=lighting,
            shot_size=shot_size,
            camera_angle=camera_angle,
            camera_motion=camera_motion,
            motion_amplitude=motion_amplitude,
            motion_speed=motion_speed,
            shot_structure=shot_structure,
            soundscape=soundscape,
            music=music,
            custom_instructions=custom_instructions,
        )
        return (presets.as_dict(),)


class MinimaxH3PromptEngineerRunningHub:
    """Rewrite user requirements into a validated MiniMax H3 prompt document."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        model_ids: list[str] = []
        for site in RUNNINGHUB_SITES:
            base_url = RunningHubClient.base_url_for_site(site)
            model_ids.extend(RunningHubClient.model_ids(base_url=base_url, timeout=2.5))
        model_ids = [DEFAULT_MODEL, *sorted(set(model_ids) - {DEFAULT_MODEL}, key=str.lower)]
        return {
            "required": {
                "runninghub_api_key": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "placeholder": "RunningHub Enterprise-Shared API Key",
                    },
                ),
                "runninghub_site": (RUNNINGHUB_SITES, {"default": SITE_GLOBAL}),
                "model": (model_ids,),
                "custom_model": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "placeholder": "Optional model ID; overrides dropdown",
                    },
                ),
                "task_mode": (TASK_MODES,),
                "user_request": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "dynamicPrompts": False,
                        "placeholder": "Describe the video, shots, cuts, dialogue, sound, and references in Chinese or English",
                    },
                ),
                "duration_seconds": (
                    "FLOAT",
                    {"default": 5.17, "min": 0.20, "max": 300.0, "step": 0.01},
                ),
                "reference_context": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "dynamicPrompts": False,
                        "placeholder": "Optional reference asset roles, speaker notes, exact dialogue, or upstream video/audio analysis",
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {"default": 0.2, "min": 0.0, "max": 2.0, "step": 0.05},
                ),
                "top_p": (
                    "FLOAT",
                    {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.05},
                ),
                "max_tokens": (
                    "INT",
                    {"default": 4096, "min": 512, "max": 32768, "step": 256},
                ),
                "reasoning_effort": (["none", "low", "medium", "high"],),
                "timeout_seconds": (
                    "INT",
                    {"default": 120, "min": 10, "max": 600, "step": 10},
                ),
                "image_max_side": (
                    "INT",
                    {"default": 1536, "min": 512, "max": 4096, "step": 128},
                ),
                "auto_repair": ("BOOLEAN", {"default": True}),
                "strict_validation": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "creative_presets": ("H3_CREATIVE_PRESET", {"forceInput": True}),
                "first_frame": ("IMAGE",),
                "last_frame": ("IMAGE",),
                "reference_images": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("formatted_prompt", "validation_report", "raw_response", "usage_json")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY
    OUTPUT_NODE = True

    @staticmethod
    def _one_image(batch: Any, name: str) -> Any:
        images = split_image_batch(batch)
        if len(images) != 1:
            raise ValueError(f"{name} must contain exactly one image, but received a batch of {len(images)}")
        return images[0]

    @classmethod
    def _collect_images(
        cls,
        *,
        task_mode: str,
        first_frame: Any = None,
        last_frame: Any = None,
        reference_images: Any = None,
        reference_context: str = "",
    ) -> list[ReferenceImage]:
        code = mode_code(task_mode)
        has_first = first_frame is not None
        has_last = last_frame is not None
        extra_images = split_image_batch(reference_images) if reference_images is not None else []

        if code == "T2VA":
            if has_first or has_last or extra_images:
                raise ValueError("T2VA does not accept reference images; choose I2VA, FL2VA, L2VA, or FULL_REFERENCE")
            return []
        if code == "I2VA":
            if not has_first:
                raise ValueError("I2VA requires first_frame")
            if has_last or extra_images:
                raise ValueError("I2VA accepts only first_frame; use FULL_REFERENCE for additional images")
            return [
                ReferenceImage(
                    "<Picture 1>", "the exact first frame at 0.00 seconds", cls._one_image(first_frame, "first_frame")
                )
            ]
        if code == "FL2VA":
            if not has_first or not has_last:
                raise ValueError("FL2VA requires both first_frame and last_frame")
            if extra_images:
                raise ValueError("FL2VA accepts only first_frame and last_frame; use FULL_REFERENCE for more images")
            return [
                ReferenceImage(
                    "<Picture 1>", "the exact first frame at 0.00 seconds", cls._one_image(first_frame, "first_frame")
                ),
                ReferenceImage(
                    "<Picture 2>",
                    "the exact final frame at the effective duration",
                    cls._one_image(last_frame, "last_frame"),
                ),
            ]
        if code == "L2VA":
            if not has_last:
                raise ValueError("L2VA requires last_frame")
            if has_first or extra_images:
                raise ValueError("L2VA accepts only last_frame; use FULL_REFERENCE for additional images")
            return [
                ReferenceImage(
                    "<Picture 1>",
                    "the exact final frame at the effective duration",
                    cls._one_image(last_frame, "last_frame"),
                )
            ]

        images: list[ReferenceImage] = []
        if has_first:
            images.append(
                ReferenceImage(
                    f"<Picture {len(images) + 1}>",
                    "a concrete first-frame anchor supplied through first_frame",
                    cls._one_image(first_frame, "first_frame"),
                )
            )
        if has_last:
            images.append(
                ReferenceImage(
                    f"<Picture {len(images) + 1}>",
                    "a concrete final-frame anchor supplied through last_frame",
                    cls._one_image(last_frame, "last_frame"),
                )
            )
        for image in extra_images:
            images.append(
                ReferenceImage(
                    f"<Picture {len(images) + 1}>",
                    "a full-reference image whose detailed role is specified by the user",
                    image,
                )
            )
        if not images and not reference_context.strip():
            raise ValueError("FULL_REFERENCE requires at least one image or a non-empty reference_context")
        return images

    @staticmethod
    def _usage_entry(result: Any, phase: str) -> dict[str, Any]:
        return {
            "phase": phase,
            "model": result.model,
            "request_id": result.request_id,
            "usage": result.usage,
        }

    def generate(
        self,
        runninghub_api_key: str,
        runninghub_site: str,
        model: str,
        custom_model: str,
        task_mode: str,
        user_request: str,
        duration_seconds: float,
        reference_context: str,
        temperature: float,
        top_p: float,
        max_tokens: int,
        reasoning_effort: str,
        timeout_seconds: int,
        image_max_side: int,
        auto_repair: bool,
        strict_validation: bool,
        creative_presets: Any = None,
        first_frame: Any = None,
        last_frame: Any = None,
        reference_images: Any = None,
    ) -> tuple[str, str, str, str]:
        if not user_request.strip():
            raise ValueError("user_request cannot be empty")
        if not runninghub_api_key.strip():
            raise ValueError("runninghub_api_key cannot be empty; use an Enterprise-Shared RunningHub API Key")

        base_url = RunningHubClient.base_url_for_site(runninghub_site)
        selected_model = custom_model.strip() or model or DEFAULT_MODEL
        duration = round(float(duration_seconds), 2)
        images = self._collect_images(
            task_mode=task_mode,
            first_frame=first_frame,
            last_frame=last_frame,
            reference_images=reference_images,
            reference_context=reference_context,
        )

        model_info = None
        try:
            site_models = RunningHubClient.list_models(base_url=base_url, timeout=2.5)
        except RunningHubError:
            # Model discovery is public but must not prevent a paid API request during a transient outage.
            site_models = None
        if site_models is not None:
            model_info = next((item for item in site_models if item.id == selected_model), None)
            if model_info is None:
                raise ValueError(
                    f"RunningHub model '{selected_model}' is not available on {runninghub_site}. "
                    "Choose a model from the site-specific dropdown or switch sites."
                )

        if images and model_info and model_info.supports_vision is False:
            raise ValueError(
                f"RunningHub model '{selected_model}' does not support vision. "
                "Choose a model whose /v1/models capabilities.vision value is true."
            )

        presets = CreativePresets.from_value(creative_presets)
        messages = build_messages(
            mode=task_mode,
            user_request=user_request,
            duration=duration,
            reference_context=reference_context,
            presets=presets,
            reference_images=images,
            image_max_side=image_max_side,
        )

        client = RunningHubClient(api_key=runninghub_api_key, base_url=base_url, timeout=timeout_seconds)
        calls: list[dict[str, Any]] = []
        raw_outputs: dict[str, str] = {}
        try:
            initial = client.chat(
                model=selected_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                reasoning_effort=reasoning_effort,
            )
            calls.append(self._usage_entry(initial, "initial"))
            raw_outputs["initial_response"] = initial.content
            formatted = clean_model_response(initial.content, task_mode)
            validation = validate_prompt(formatted, task_mode, duration)

            if not validation.is_valid and auto_repair:
                repair = client.chat(
                    model=selected_model,
                    messages=build_repair_messages(
                        mode=task_mode,
                        duration=duration,
                        previous_response=formatted,
                        validation_report=validation.report(),
                    ),
                    max_tokens=max_tokens,
                    temperature=0.0,
                    top_p=1.0,
                    reasoning_effort="none",
                )
                calls.append(self._usage_entry(repair, "repair"))
                raw_outputs["repair_response"] = repair.content
                formatted = clean_model_response(repair.content, task_mode)
                validation = validate_prompt(formatted, task_mode, duration)
        except RunningHubError as exc:
            raise RuntimeError(exc.user_message()) from exc

        report = validation.report()
        if strict_validation and not validation.is_valid:
            raise ValueError(
                "RunningHub returned a prompt that still fails strict H3 validation after repair:\n" + report
            )

        usage = {
            "provider": "RunningHub",
            "site": runninghub_site,
            "endpoint": f"{base_url}/chat/completions",
            "selected_model": selected_model,
            "calls": calls,
        }
        return (
            formatted,
            report,
            json.dumps(raw_outputs, ensure_ascii=False, indent=2),
            json.dumps(usage, ensure_ascii=False, indent=2),
        )


NODE_CLASS_MAPPINGS = {
    "H3CreativePresets": H3CreativePresetsNode,
    "MinimaxH3PromptEngineerRunningHub": MinimaxH3PromptEngineerRunningHub,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "H3CreativePresets": "H3 Creative Presets",
    "MinimaxH3PromptEngineerRunningHub": "Minimax H3 Prompt Engineer · RunningHub",
}
