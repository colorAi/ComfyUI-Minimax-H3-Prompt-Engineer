// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 colorAi

const PROVIDER_WIDGET_NAME = "ai_provider";
const PROVIDER_FIELD_PREFIX = `${PROVIDER_WIDGET_NAME}.`;
const WRAPPED_FLAG = "__h3ProviderMemoryWrapped";

function providerFields(node) {
    return (node.widgets ?? []).filter((widget) => String(widget?.name ?? "").startsWith(PROVIDER_FIELD_PREFIX));
}

function fieldName(widget) {
    return String(widget.name).slice(PROVIDER_FIELD_PREFIX.length);
}

function rememberVisibleFields(node, state) {
    if (!state.currentProvider) return;
    const values = state.cache.get(state.currentProvider) ?? new Map();
    for (const widget of providerFields(node)) values.set(fieldName(widget), widget.value);
    state.cache.set(state.currentProvider, values);
}

function wrapFieldCallbacks(node, state) {
    for (const widget of providerFields(node)) {
        if (widget[WRAPPED_FLAG]) continue;
        widget[WRAPPED_FLAG] = true;
        const originalCallback = widget.callback;
        widget.callback = function (value) {
            const result = originalCallback?.apply(this, arguments);
            if (state.currentProvider) {
                const values = state.cache.get(state.currentProvider) ?? new Map();
                values.set(fieldName(widget), widget.value ?? value);
                state.cache.set(state.currentProvider, values);
            }
            return result;
        };
    }
}

function restoreVisibleFields(node, state) {
    const values = state.cache.get(state.currentProvider);
    if (!values) return;
    for (const widget of providerFields(node)) {
        const name = fieldName(widget);
        if (values.has(name)) widget.value = values.get(name);
    }
}

export function installProviderConfigMemory(node) {
    const providerWidget = node.widgets?.find((widget) => widget.name === PROVIDER_WIDGET_NAME);
    if (!providerWidget || node.__h3ProviderConfigMemoryCleanup) return () => {};

    const state = {
        cache: new Map(),
        currentProvider: String(providerWidget.value ?? ""),
    };
    let disposed = false;

    function sync() {
        if (disposed) return;
        const nextProvider = String(providerWidget.value ?? "");
        if (nextProvider !== state.currentProvider) {
            state.currentProvider = nextProvider;
            restoreVisibleFields(node, state);
        }
        wrapFieldCallbacks(node, state);
        rememberVisibleFields(node, state);
    }

    rememberVisibleFields(node, state);
    wrapFieldCallbacks(node, state);

    const originalProviderCallback = providerWidget.callback;
    providerWidget.callback = function () {
        // DynamicCombo removes the previous provider's child widgets inside its
        // callback, so capture their latest values before handing control back.
        rememberVisibleFields(node, state);
        const result = originalProviderCallback?.apply(this, arguments);
        queueMicrotask(sync);
        return result;
    };
    const intervalId = window.setInterval(sync, 250);

    const cleanup = () => {
        disposed = true;
        window.clearInterval(intervalId);
        providerWidget.callback = originalProviderCallback;
        state.cache.clear();
        node.__h3ProviderConfigMemoryCleanup = null;
    };
    node.__h3ProviderConfigMemoryCleanup = cleanup;
    return cleanup;
}
