# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Conversion helpers for ComfyUI IMAGE tensors and OpenAI image_url parts."""

from __future__ import annotations

import base64
import io
from typing import Any

import numpy as np
from PIL import Image


def split_image_batch(batch: Any) -> list[Any]:
    if batch is None:
        return []
    shape = getattr(batch, "shape", None)
    if shape is None or len(shape) != 4:
        raise ValueError("Expected a ComfyUI IMAGE batch with shape [B,H,W,C]")
    return [batch[index : index + 1] for index in range(int(shape[0]))]


def image_tensor_to_data_url(image: Any, *, max_side: int = 1536, quality: int = 90) -> str:
    """Encode one [1,H,W,C] ComfyUI image as a resized JPEG data URL."""
    if hasattr(image, "detach"):
        image = image.detach()
    if hasattr(image, "cpu"):
        image = image.cpu()
    if hasattr(image, "numpy"):
        image = image.numpy()
    array = np.asarray(image)
    if array.ndim == 4:
        if array.shape[0] < 1:
            raise ValueError("Image batch is empty")
        array = array[0]
    if array.ndim != 3 or array.shape[-1] < 3:
        raise ValueError("Expected an RGB ComfyUI image")
    array = np.clip(array[..., :3], 0.0, 1.0)
    array = (array * 255.0 + 0.5).astype(np.uint8)
    pil_image = Image.fromarray(array, mode="RGB")

    max_side = max(256, int(max_side))
    if max(pil_image.size) > max_side:
        scale = max_side / max(pil_image.size)
        size = (max(1, round(pil_image.width * scale)), max(1, round(pil_image.height * scale)))
        pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=max(40, min(95, int(quality))), optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def image_url_part(image: Any, *, max_side: int = 1536) -> dict[str, Any]:
    return {
        "type": "image_url",
        "image_url": {
            "url": image_tensor_to_data_url(image, max_side=max_side),
            "detail": "high",
        },
    }
