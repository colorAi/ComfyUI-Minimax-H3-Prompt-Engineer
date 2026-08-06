# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

"""Same-origin ComfyUI routes for local AI-provider configuration."""

from __future__ import annotations

import json

from aiohttp import web
from server import PromptServer

from .provider_config_store import load_provider_configs, save_provider_config

routes = PromptServer.instance.routes


@routes.get("/minimax-h3-prompt-engineer/provider-config")
async def get_provider_config(_request: web.Request) -> web.Response:
    return web.json_response({"providers": load_provider_configs()})


@routes.post("/minimax-h3-prompt-engineer/provider-config")
async def set_provider_config(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise TypeError("Request body must be a JSON object")
        provider = payload.get("provider")
        if not isinstance(provider, str):
            raise TypeError("provider must be a string")
        config = save_provider_config(provider, payload.get("config"))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response({"provider": provider, "config": config})
