// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 colorAi

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

globalThis.window = globalThis;

const source = await readFile(new URL("../web/h3_provider_config_memory.js", import.meta.url), "utf8");
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
const { installProviderConfigMemory } = await import(moduleUrl);

const localProvider = "Local OpenAI-compatible";
const directProvider = "Direct · Use prompt as-is";
const field = (name, value) => ({ name: `ai_provider.${name}`, value, callback() {} });
const localFields = [field("base_url", "http://127.0.0.1:11434/v1"), field("model", "qwen"), field("api_key", "")];
const restoredFields = [field("base_url", "http://127.0.0.1:11434/v1"), field("model", "default"), field("api_key", "")];
let node;
const provider = {
    name: "ai_provider",
    value: localProvider,
    callback() {
        node.widgets = this.value === localProvider ? [provider, ...restoredFields] : [provider];
    },
};
node = { widgets: [provider, ...localFields] };
const cleanup = installProviderConfigMemory(node);

localFields[0].value = "http://192.168.1.10:8000/v1";
localFields[1].value = "qwen3-vl:8b";
localFields[2].value = "local-secret";

provider.value = directProvider;
provider.callback(provider.value);
await Promise.resolve();

provider.value = localProvider;
provider.callback(provider.value);
await Promise.resolve();

assert.equal(restoredFields[0].value, "http://192.168.1.10:8000/v1");
assert.equal(restoredFields[1].value, "qwen3-vl:8b");
assert.equal(restoredFields[2].value, "local-secret");

cleanup();
process.stdout.write("provider config memory: PASS\n");
