// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 colorAi

const PROVIDER_WIDGET_NAME = "ai_provider";
const PROVIDER_FIELD_PREFIX = `${PROVIDER_WIDGET_NAME}.`;
const WRAPPED_FLAG = "__h3ProviderMemoryWrapped";
const CONFIG_ENDPOINT = "/minimax-h3-prompt-engineer/provider-config";
const PERSISTENT_PROVIDERS = new Set(["RunningHub", "OpenAI", "Local OpenAI-compatible"]);
const DEFAULT_RESTORE_SETTLE_MS = 1200;
const DEFAULT_SAVE_DEBOUNCE_MS = 300;

let sharedConfigPromise;

function providerFields(node) {
    return (node.widgets ?? []).filter((widget) => String(widget?.name ?? "").startsWith(PROVIDER_FIELD_PREFIX));
}

function fieldName(widget) {
    return String(widget.name).slice(PROVIDER_FIELD_PREFIX.length);
}

function providerMap(values = {}) {
    return new Map(Object.entries(values).filter(([, value]) => typeof value === "string"));
}

function providerObject(values) {
    return Object.fromEntries(values ?? []);
}

async function loadPersistentConfigs() {
    if (!sharedConfigPromise) {
        sharedConfigPromise = fetch(CONFIG_ENDPOINT, {
            credentials: "same-origin",
            cache: "no-store",
        }).then(async (response) => {
            if (!response.ok) throw new Error(`config load failed with HTTP ${response.status}`);
            const payload = await response.json();
            return payload?.providers && typeof payload.providers === "object" ? payload.providers : {};
        }).catch((error) => {
            sharedConfigPromise = null;
            throw error;
        });
    }
    return sharedConfigPromise;
}

async function savePersistentProvider(provider, values, keepalive = false) {
    if (!PERSISTENT_PROVIDERS.has(provider)) return;
    const response = await fetch(CONFIG_ENDPOINT, {
        method: "POST",
        credentials: "same-origin",
        keepalive,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, config: providerObject(values) }),
    });
    if (!response.ok) throw new Error(`config save failed with HTTP ${response.status}`);
    const payload = await response.json();
    if (sharedConfigPromise) {
        void sharedConfigPromise.then((providers) => {
            providers[provider] = payload?.config ?? providerObject(values);
        });
    }
}

function rememberVisibleFields(node, state, provider = state.currentProvider) {
    if (!PERSISTENT_PROVIDERS.has(provider)) return false;
    const values = state.cache.get(provider) ?? new Map();
    let changed = false;
    for (const widget of providerFields(node)) {
        const name = fieldName(widget);
        if (!values.has(name) || values.get(name) !== widget.value) changed = true;
        values.set(name, widget.value);
    }
    state.cache.set(provider, values);
    return changed;
}

function restoreVisibleFields(node, state) {
    const values = state.cache.get(state.currentProvider);
    if (!values) return;
    for (const widget of providerFields(node)) {
        const name = fieldName(widget);
        if (values.has(name) && widget.value !== values.get(name)) widget.value = values.get(name);
    }
}

export function installProviderConfigMemory(node, options = {}) {
    const providerWidget = node.widgets?.find((widget) => widget.name === PROVIDER_WIDGET_NAME);
    if (!providerWidget || node.__h3ProviderConfigMemoryCleanup) return () => {};

    const loadConfig = options.loadConfig ?? loadPersistentConfigs;
    const saveConfig = options.saveConfig ?? savePersistentProvider;
    const restoreSettleMs = options.restoreSettleMs ?? DEFAULT_RESTORE_SETTLE_MS;
    const saveDebounceMs = options.saveDebounceMs ?? DEFAULT_SAVE_DEBOUNCE_MS;
    const intervalMs = options.intervalMs ?? 100;
    const state = {
        cache: new Map(),
        currentProvider: String(providerWidget.value ?? ""),
        persistenceReady: false,
        restoreUntil: 0,
        touchedProviders: new Set(),
    };
    const saveTimers = new Map();
    let disposed = false;

    function persist(provider, keepalive = false) {
        if (!state.persistenceReady || !PERSISTENT_PROVIDERS.has(provider)) return;
        const values = state.cache.get(provider);
        if (!values) return;
        void saveConfig(provider, new Map(values), keepalive).catch((error) => {
            console.warn("MiniMax H3 provider config could not be saved:", error);
        });
    }

    function schedulePersist(provider) {
        if (!state.persistenceReady || !PERSISTENT_PROVIDERS.has(provider)) return;
        window.clearTimeout(saveTimers.get(provider));
        saveTimers.set(provider, window.setTimeout(() => {
            saveTimers.delete(provider);
            persist(provider);
        }, saveDebounceMs));
    }

    function markProviderChanged(provider) {
        state.touchedProviders.add(provider);
        schedulePersist(provider);
    }

    function wrapFieldCallbacks() {
        for (const widget of providerFields(node)) {
            if (widget[WRAPPED_FLAG]) continue;
            widget[WRAPPED_FLAG] = true;
            const originalCallback = widget.callback;
            widget.callback = function (value) {
                const result = originalCallback?.apply(this, arguments);
                const provider = state.currentProvider;
                if (PERSISTENT_PROVIDERS.has(provider)) {
                    const values = state.cache.get(provider) ?? new Map();
                    values.set(fieldName(widget), widget.value ?? value);
                    state.cache.set(provider, values);
                    markProviderChanged(provider);
                }
                return result;
            };
        }
    }

    function beginRestore() {
        state.restoreUntil = Date.now() + restoreSettleMs;
        restoreVisibleFields(node, state);
    }

    function sync() {
        if (disposed) return;
        const nextProvider = String(providerWidget.value ?? "");
        if (nextProvider !== state.currentProvider) {
            state.currentProvider = nextProvider;
            beginRestore();
        }
        wrapFieldCallbacks();
        if (Date.now() < state.restoreUntil) {
            // DynamicCombo may initialize its replacement child widgets more
            // than once. Keep restoring through that short settling window.
            restoreVisibleFields(node, state);
        } else if (rememberVisibleFields(node, state)) {
            markProviderChanged(state.currentProvider);
        }
    }

    rememberVisibleFields(node, state);
    wrapFieldCallbacks();

    const originalProviderCallback = providerWidget.callback;
    providerWidget.callback = function () {
        const previousProvider = state.currentProvider;
        if (rememberVisibleFields(node, state, previousProvider)) markProviderChanged(previousProvider);
        schedulePersist(previousProvider);
        const result = originalProviderCallback?.apply(this, arguments);
        queueMicrotask(sync);
        return result;
    };

    void loadConfig().then((providers) => {
        if (disposed) return;
        for (const [provider, values] of Object.entries(providers ?? {})) {
            if (!PERSISTENT_PROVIDERS.has(provider) || state.touchedProviders.has(provider)) continue;
            state.cache.set(provider, providerMap(values));
        }
        state.persistenceReady = true;
        beginRestore();
        sync();
    }).catch((error) => {
        state.persistenceReady = true;
        console.warn("MiniMax H3 provider config could not be loaded:", error);
    });

    const intervalId = window.setInterval(sync, intervalMs);
    const flushBeforeUnload = () => {
        rememberVisibleFields(node, state);
        persist(state.currentProvider, true);
    };
    window.addEventListener?.("beforeunload", flushBeforeUnload);

    const cleanup = () => {
        rememberVisibleFields(node, state);
        persist(state.currentProvider, true);
        disposed = true;
        window.clearInterval(intervalId);
        for (const timerId of saveTimers.values()) window.clearTimeout(timerId);
        saveTimers.clear();
        window.removeEventListener?.("beforeunload", flushBeforeUnload);
        providerWidget.callback = originalProviderCallback;
        state.cache.clear();
        node.__h3ProviderConfigMemoryCleanup = null;
    };
    node.__h3ProviderConfigMemoryCleanup = cleanup;
    return cleanup;
}
