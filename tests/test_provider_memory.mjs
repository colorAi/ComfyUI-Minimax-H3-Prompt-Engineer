// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 colorAi

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

globalThis.window = globalThis;
globalThis.addEventListener = () => {};
globalThis.removeEventListener = () => {};

const source = await readFile(new URL("../web/h3_provider_config_memory.js", import.meta.url), "utf8");
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
const { installProviderConfigMemory } = await import(moduleUrl);

const providers = {
    runninghub: "RunningHub",
    openai: "OpenAI",
    local: "Local OpenAI-compatible",
    direct: "Direct · Use prompt as-is",
};
const defaults = {
    [providers.runninghub]: { api_key: "", site: "RunningHub Global (.ai)", model: "MiniMax-Hailuo-02" },
    [providers.openai]: { api_key: "", base_url: "https://api.openai.com/v1", model: "gpt-5" },
    [providers.local]: { api_key: "", base_url: "http://127.0.0.1:11434/v1", model: "qwen" },
    [providers.direct]: {},
};
const configured = {
    [providers.runninghub]: { api_key: "rh-secret", site: "RunningHub China (.cn)", model: "MiniMax-H3" },
    [providers.openai]: { api_key: "sk-openai", base_url: "https://gateway.example/v1", model: "gpt-5.2" },
    [providers.local]: { api_key: "local-secret", base_url: "http://192.168.1.10:8000/v1", model: "qwen3-vl:8b" },
};

const field = (name, value) => ({ name: `ai_provider.${name}`, value, callback() {} });
const makeFields = (provider) => Object.entries(defaults[provider]).map(([name, value]) => field(name, value));
const currentValues = (node) => Object.fromEntries(
    node.widgets.slice(1).map((widget) => [widget.name.slice("ai_provider.".length), widget.value]),
);
const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

let node;
const providerWidget = {
    name: "ai_provider",
    value: providers.local,
    callback() {
        node.widgets = [providerWidget, ...makeFields(this.value)];
        // Reproduce DynamicCombo's delayed replacement/default initialization.
        setTimeout(() => {
            node.widgets = [providerWidget, ...makeFields(this.value)];
        }, 1);
    },
};
node = { widgets: [providerWidget, ...makeFields(providerWidget.value)] };
const saved = {};
const cleanup = installProviderConfigMemory(node, {
    loadConfig: async () => ({}),
    saveConfig: async (provider, values) => {
        saved[provider] = Object.fromEntries(values);
    },
    intervalMs: 2,
    restoreSettleMs: 30,
    saveDebounceMs: 1,
});
await wait(5);

for (const nextProvider of [providers.local, providers.openai, providers.runninghub]) {
    if (providerWidget.value !== nextProvider) {
        providerWidget.value = nextProvider;
        providerWidget.callback(nextProvider);
        await wait(5);
    }
    for (const widget of node.widgets.slice(1)) {
        widget.value = configured[nextProvider][widget.name.slice("ai_provider.".length)];
    }
}

for (const expectedProvider of [providers.direct, providers.local, providers.openai, providers.runninghub]) {
    providerWidget.value = expectedProvider;
    providerWidget.callback(expectedProvider);
    await wait(35);
    if (configured[expectedProvider]) assert.deepEqual(currentValues(node), configured[expectedProvider]);
}

await wait(5);
for (const expectedProvider of [providers.local, providers.openai, providers.runninghub]) {
    assert.deepEqual(saved[expectedProvider], configured[expectedProvider]);
}

cleanup();
process.stdout.write("provider config switching and persistence: PASS\n");
