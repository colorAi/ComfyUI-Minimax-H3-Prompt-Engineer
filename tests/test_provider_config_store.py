# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 colorAi

from __future__ import annotations

import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import provider_config_store


class ProviderConfigStoreTests(unittest.TestCase):
    def test_provider_settings_are_saved_atomically_and_reloaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "provider_config.json"
            with patch.object(provider_config_store, "CONFIG_PATH", config_path):
                saved = provider_config_store.save_provider_config(
                    "Local OpenAI-compatible",
                    {
                        "base_url": "http://192.168.1.10:8000/v1",
                        "model": "qwen3-vl:8b",
                        "api_key": "local-secret",
                        "ignored": "not-written",
                    },
                )
                self.assertEqual(
                    saved,
                    {
                        "base_url": "http://192.168.1.10:8000/v1",
                        "model": "qwen3-vl:8b",
                        "api_key": "local-secret",
                    },
                )
                self.assertEqual(provider_config_store.load_provider_configs()["Local OpenAI-compatible"], saved)
                payload = json.loads(config_path.read_text(encoding="utf-8"))
                self.assertEqual(payload["version"], 1)
                self.assertNotIn("ignored", payload["providers"]["Local OpenAI-compatible"])
                self.assertFalse(config_path.with_suffix(".json.tmp").exists())
                if hasattr(stat, "S_IMODE"):
                    self.assertEqual(stat.S_IMODE(config_path.stat().st_mode), 0o600)

    def test_direct_provider_cannot_be_persisted(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(provider_config_store, "CONFIG_PATH", Path(directory) / "provider_config.json"),
            self.assertRaisesRegex(ValueError, "Unsupported persistent provider"),
        ):
            provider_config_store.save_provider_config("Direct · Use prompt as-is", {})


if __name__ == "__main__":
    unittest.main()
