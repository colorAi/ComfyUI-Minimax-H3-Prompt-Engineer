# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Creative preset definitions shared by the ComfyUI nodes and prompt builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

AUTO = "Auto"

VISUAL_STYLES = [
    AUTO,
    "Cinematic Live-action",
    "Realistic Documentary",
    "Commercial Product Film",
    "2D Animation",
    "3D CG",
    "Claymation",
    "Watercolor",
    "Vintage Film",
    "Custom",
]

ENVIRONMENTS = [
    AUTO,
    "Indoor",
    "Outdoor",
    "Urban Street",
    "Natural Landscape",
    "Studio",
    "Stage",
    "Industrial",
    "Custom",
]

TIME_WEATHER = [
    AUTO,
    "Daylight",
    "Night",
    "Sunrise",
    "Golden Hour",
    "Blue Hour",
    "Overcast",
    "Rain",
    "Snow",
    "Fog",
    "Custom",
]

LIGHTING = [
    AUTO,
    "Natural Daylight",
    "Soft Diffused Light",
    "Golden-hour Light",
    "Low-key Cinematic",
    "High-key Studio",
    "Neon Night",
    "Strong Backlight",
    "Side Lighting",
    "Silhouette",
    "Custom",
]

SHOT_SIZES = [
    AUTO,
    "Extreme Wide",
    "Wide",
    "Medium Wide",
    "Medium",
    "Medium Close-up",
    "Close-up",
    "Extreme Close-up",
    "POV",
]

CAMERA_ANGLES = [
    AUTO,
    "Eye Level",
    "Low Angle",
    "High Angle",
    "Bird's-eye View",
    "Over-the-shoulder",
    "Dutch Angle",
    "Custom",
]

CAMERA_MOTIONS = [
    AUTO,
    "Static Shot",
    "Zoom In",
    "Zoom Out",
    "Push In",
    "Pull Out",
    "Pan Left",
    "Pan Right",
    "Truck Left",
    "Truck Right",
    "Tilt Up",
    "Tilt Down",
    "Pedestal Up",
    "Pedestal Down",
    "Arc Shot",
    "Tracking Shot",
    "Shake Slightly",
    "Shake Strongly",
    "POV",
    "Roll Clockwise",
    "Roll Counterclockwise",
]

MOTION_AMPLITUDES = [
    "Default (omit amplitude)",
    "with small amplitude",
    "with large amplitude",
]

MOTION_SPEEDS = [
    "Default (omit speed)",
    "at slow speed",
    "at fast speed",
]

SHOT_STRUCTURES = [
    AUTO,
    "Single Continuous Shot",
    "Multi-shot Narrative",
    "Fast-cut Sequence",
    "Slow-paced Sequence",
]

SOUNDSCAPES = [
    AUTO,
    "Realistic Detailed",
    "Minimal",
    "Complete Silence",
]

MUSIC = [
    AUTO,
    "No Music",
    "Piano and Strings",
    "Electronic Pulse",
    "Acoustic",
    "Orchestral",
    "Custom",
]


@dataclass(slots=True)
class CreativePresets:
    visual_style: str = AUTO
    environment: str = AUTO
    time_weather: str = AUTO
    lighting: str = AUTO
    shot_size: str = AUTO
    camera_angle: str = AUTO
    camera_motion: str = AUTO
    motion_amplitude: str = MOTION_AMPLITUDES[0]
    motion_speed: str = MOTION_SPEEDS[0]
    shot_structure: str = AUTO
    soundscape: str = AUTO
    music: str = AUTO
    custom_instructions: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_value(cls, value: Any) -> CreativePresets:
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            known = {name for name in cls.__dataclass_fields__ if name != "extra"}
            kwargs = {key: item for key, item in value.items() if key in known}
            extras = {key: item for key, item in value.items() if key not in known}
            return cls(**kwargs, extra=extras)
        return cls()

    def active_constraints(self) -> list[str]:
        """Return explicit English constraints; Auto/default selections are omitted."""
        pairs = [
            ("Visual style", self.visual_style, AUTO),
            ("Environment", self.environment, AUTO),
            ("Time or weather", self.time_weather, AUTO),
            ("Lighting", self.lighting, AUTO),
            ("Shot size", self.shot_size, AUTO),
            ("Camera angle", self.camera_angle, AUTO),
            ("Camera motion", self.camera_motion, AUTO),
            ("Motion amplitude", self.motion_amplitude, MOTION_AMPLITUDES[0]),
            ("Motion speed", self.motion_speed, MOTION_SPEEDS[0]),
            ("Shot structure", self.shot_structure, AUTO),
            ("Overall soundscape treatment", self.soundscape, AUTO),
            ("Non-diegetic music treatment", self.music, AUTO),
        ]
        constraints = [f"{label}: {value}." for label, value, ignored in pairs if value != ignored]
        if self.custom_instructions.strip():
            constraints.append(f"Additional creative constraint: {self.custom_instructions.strip()}")
        return constraints

    def as_dict(self) -> dict[str, Any]:
        return {
            "visual_style": self.visual_style,
            "environment": self.environment,
            "time_weather": self.time_weather,
            "lighting": self.lighting,
            "shot_size": self.shot_size,
            "camera_angle": self.camera_angle,
            "camera_motion": self.camera_motion,
            "motion_amplitude": self.motion_amplitude,
            "motion_speed": self.motion_speed,
            "shot_structure": self.shot_structure,
            "soundscape": self.soundscape,
            "music": self.music,
            "custom_instructions": self.custom_instructions,
            **self.extra,
        }
