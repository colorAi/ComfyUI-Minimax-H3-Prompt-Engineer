// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 colorAi

import { app } from "../../scripts/app.js";

const NODE_TYPE = "MinimaxH3PromptEngineerRunningHub";
const DEFAULT_MODEL = "qwen/qwen3.6-plus";
const SITE_ENDPOINTS = {
    "RunningHub Global (.ai)": "https://llm.runninghub.ai/v1/models",
    "RunningHub China (.cn)": "https://llm.runninghub.cn/v1/models",
};
const FALLBACK_MODELS = {
    "RunningHub Global (.ai)": [
        DEFAULT_MODEL,
        "google/gemini-3.5-flash-lite",
        "minimax/minimax-m2.7",
        "bytedance/doubao-seed-2.0-mini",
        "glm-5.2",
    ],
    "RunningHub China (.cn)": [
        DEFAULT_MODEL,
        "qwen/qwen3.7-plus",
        "glm-5v-turbo",
        "minimax/minimax-m2.7",
        "bytedance/doubao-seed-2.0-mini",
        "glm-5.2",
    ],
};
const modelCache = new Map();

function orderedModelIds(ids) {
    const unique = [...new Set(ids.filter((id) => typeof id === "string" && id.length > 0))];
    unique.sort((a, b) => a.localeCompare(b));
    return unique.includes(DEFAULT_MODEL)
        ? [DEFAULT_MODEL, ...unique.filter((id) => id !== DEFAULT_MODEL)]
        : unique;
}

async function loadModels(site) {
    if (modelCache.has(site)) {
        return modelCache.get(site);
    }
    const endpoint = SITE_ENDPOINTS[site];
    if (!endpoint) {
        return FALLBACK_MODELS["RunningHub Global (.ai)"];
    }
    try {
        const response = await fetch(endpoint, { headers: { Accept: "application/json" } });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const payload = await response.json();
        const models = orderedModelIds((payload.data ?? []).map((item) => item?.id));
        if (models.length === 0) {
            throw new Error("RunningHub returned an empty model list");
        }
        modelCache.set(site, models);
        return models;
    } catch (error) {
        console.warn(`[MiniMax H3] Could not refresh ${site} models; using fallback list.`, error);
        return FALLBACK_MODELS[site] ?? FALLBACK_MODELS["RunningHub Global (.ai)"];
    }
}

async function refreshModelWidget(node, site) {
    const modelWidget = node.widgets?.find((widget) => widget.name === "model");
    if (!modelWidget) {
        return;
    }
    const models = await loadModels(site);
    const currentSite = node.widgets?.find((widget) => widget.name === "runninghub_site")?.value;
    if (currentSite !== site) {
        return;
    }
    modelWidget.options = modelWidget.options ?? {};
    modelWidget.options.values = models;
    if (!models.includes(modelWidget.value)) {
        modelWidget.value = models.includes(DEFAULT_MODEL) ? DEFAULT_MODEL : models[0];
        modelWidget.callback?.(modelWidget.value);
    }
    node.setDirtyCanvas?.(true, true);
}

app.registerExtension({
    name: "MiniMaxH3.RunningHubSiteModels",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_TYPE) {
            return;
        }

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalOnNodeCreated?.apply(this, arguments);
            const siteWidget = this.widgets?.find((widget) => widget.name === "runninghub_site");
            if (siteWidget) {
                const thisNode = this;
                const originalCallback = siteWidget.callback;
                siteWidget.callback = function (value) {
                    const callbackResult = originalCallback?.apply(this, arguments);
                    void refreshModelWidget(thisNode, value);
                    return callbackResult;
                };
                setTimeout(() => void refreshModelWidget(thisNode, siteWidget.value), 0);
            }
            return result;
        };

        const originalOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = originalOnConfigure?.apply(this, arguments);
            const site = this.widgets?.find((widget) => widget.name === "runninghub_site")?.value;
            if (site) {
                setTimeout(() => void refreshModelWidget(this, site), 0);
            }
            return result;
        };
    },
});
