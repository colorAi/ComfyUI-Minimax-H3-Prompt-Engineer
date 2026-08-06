// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 colorAi

import { app } from "../../scripts/app.js";

const NODE_TYPE = "MinimaxH3PromptStudio";
const INSTALLED_FLAG = "__h3AssetAutocompleteInstalled";
const PROMPT_EDITOR_HEIGHT = 112;
const DOM_WIDGET_VERTICAL_MARGIN = 20;
const PROMPT_WIDGET_HEIGHT = PROMPT_EDITOR_HEIGHT + DOM_WIDGET_VERTICAL_MARGIN;

function numericSuffix(name) {
    const match = String(name ?? "").match(/(\d+)$/);
    return match ? Number(match[1]) : Number.MAX_SAFE_INTEGER;
}

function isConnected(input) {
    return input?.link != null || (Array.isArray(input?.links) && input.links.length > 0);
}

function connectedByPattern(node, pattern) {
    return (node.inputs ?? [])
        .filter((input) => pattern.test(String(input?.name ?? "")) && isConnected(input))
        .sort((left, right) => numericSuffix(left.name) - numericSuffix(right.name));
}

function linkedSourceLabel(node, input) {
    const linkId = input?.link ?? input?.links?.[0];
    const graph = node.graph ?? app.graph;
    const links = graph?.links;
    const link = links?.get?.(linkId) ?? links?.[linkId];
    const originId = link?.origin_id ?? link?.originId;
    const source = originId != null ? graph?.getNodeById?.(originId) : null;
    return source?.title || source?.type || String(input?.name ?? "material");
}

function suggestion(alias, alternate, nativeLabel, kind, source) {
    return { alias, alternate, nativeLabel, kind, source };
}

function collectAssetSuggestions(node) {
    const refImages = connectedByPattern(node, /ref_image_\d+$/);
    const refVideos = connectedByPattern(node, /ref_video_\d+$/);
    const videoAudios = connectedByPattern(node, /ref_video_audio_\d+$/);
    const refAudios = connectedByPattern(node, /ref_audio_\d+$/);
    const hasFullReference = refImages.length || refVideos.length || videoAudios.length || refAudios.length;
    const items = [];

    if (!hasFullReference) {
        const firstFrame = (node.inputs ?? []).find((input) => input.name === "first_frame" && isConnected(input));
        const lastFrame = (node.inputs ?? []).find((input) => input.name === "last_frame" && isConnected(input));
        let pictureNumber = 0;
        for (const [input, role] of [[firstFrame, "首帧"], [lastFrame, "尾帧"]]) {
            if (!input) continue;
            pictureNumber += 1;
            items.push(suggestion(
                `@图像${pictureNumber}`,
                `@image${pictureNumber}`,
                `<Picture ${pictureNumber}>`,
                role,
                linkedSourceLabel(node, input),
            ));
        }
        return items;
    }

    refImages.forEach((input, index) => {
        const number = index + 1;
        items.push(suggestion(
            `@图像${number}`,
            `@image${number}`,
            `<Picture ${number}>`,
            "参考图像",
            linkedSourceLabel(node, input),
        ));
    });

    let nativeAudioNumber = 0;
    refVideos.forEach((input, index) => {
        const number = index + 1;
        items.push(suggestion(
            `@视频${number}`,
            `@video${number}`,
            `<Video ${number}>`,
            "参考视频",
            linkedSourceLabel(node, input),
        ));

        const suffix = numericSuffix(input.name);
        const pairedAudio = videoAudios.find((audioInput) => numericSuffix(audioInput.name) === suffix);
        if (pairedAudio) {
            nativeAudioNumber += 1;
            items.push(suggestion(
                `@视频音频${number}`,
                `@video_audio${number}`,
                `<Audio ${nativeAudioNumber}>`,
                "视频配套音频",
                linkedSourceLabel(node, pairedAudio),
            ));
        }
    });

    refAudios.forEach((input, index) => {
        nativeAudioNumber += 1;
        const number = index + 1;
        items.push(suggestion(
            `@音频${number}`,
            `@audio${number}`,
            `<Audio ${nativeAudioNumber}>`,
            "独立参考音频",
            linkedSourceLabel(node, input),
        ));
    });
    return items;
}

function activeAtToken(input) {
    const cursor = input.selectionStart ?? input.value.length;
    const before = input.value.slice(0, cursor);
    const match = before.match(/(?:^|[\s，。；：、,;:(（])(@[^@\s]*)$/);
    if (!match) return null;
    const token = match[1];
    return {
        start: cursor - token.length,
        end: cursor,
        query: token.slice(1).toLocaleLowerCase(),
    };
}

function ensureStyles() {
    if (document.getElementById("h3-asset-autocomplete-style")) return;
    const style = document.createElement("style");
    style.id = "h3-asset-autocomplete-style";
    style.textContent = `
        .h3-asset-autocomplete {
            position: fixed; z-index: 100000; min-width: 320px; max-width: 520px;
            max-height: 280px; overflow-y: auto; padding: 6px;
            border: 1px solid color-mix(in srgb, var(--border-color, #888) 70%, transparent);
            border-radius: 8px; background: var(--comfy-menu-bg, #202124);
            color: var(--input-text, #f1f3f4); box-shadow: 0 10px 30px #0008;
            font: 12px/1.35 sans-serif;
        }
        .h3-asset-autocomplete-item { padding: 7px 9px; border-radius: 6px; cursor: pointer; }
        .h3-asset-autocomplete-item.active { background: var(--comfy-input-bg, #3b3d40); }
        .h3-asset-autocomplete-title { display: flex; gap: 8px; align-items: baseline; }
        .h3-asset-autocomplete-alias { color: #8ab4f8; font-weight: 700; }
        .h3-asset-autocomplete-native { color: #c4c7c5; }
        .h3-asset-autocomplete-meta { color: #9aa0a6; margin-top: 2px; }
        .h3-asset-autocomplete-empty { padding: 9px; color: #9aa0a6; }
    `;
    document.head.appendChild(style);
}

function applyPromptWidgetHeight(node, widget, input) {
    if (widget.__h3PromptHeightApplied) return;
    widget.__h3PromptHeightApplied = true;
    widget.options ??= {};
    widget.options.getMinHeight = () => PROMPT_WIDGET_HEIGHT;
    widget.options.getHeight = () => PROMPT_WIDGET_HEIGHT;

    // Re-run LiteGraph's DOM-widget layout with the new minimum. Keeping the
    // requested node size unchanged lets the layout engine grow it only when
    // the current height cannot accommodate the larger prompt editor.
    if (Array.isArray(node.size)) node.setSize?.([node.size[0], node.size[1]]);
    node.graph?.setDirtyCanvas?.(true, true);
}

function attachAutocomplete(node, widget, input) {
    if (input.dataset.h3AssetAutocomplete === "1") return () => {};
    input.dataset.h3AssetAutocomplete = "1";
    applyPromptWidgetHeight(node, widget, input);
    ensureStyles();

    const menu = document.createElement("div");
    menu.className = "h3-asset-autocomplete";
    menu.hidden = true;
    document.body.appendChild(menu);
    let activeIndex = 0;
    let current = [];
    let token = null;

    function close() {
        menu.hidden = true;
        current = [];
        token = null;
    }

    function positionMenu() {
        const rect = input.getBoundingClientRect();
        menu.style.left = `${Math.max(8, Math.min(rect.left, window.innerWidth - 540))}px`;
        menu.style.top = `${Math.min(rect.bottom + 4, window.innerHeight - 290)}px`;
        menu.style.width = `${Math.max(320, rect.width)}px`;
    }

    function choose(item) {
        if (!token) return;
        const before = input.value.slice(0, token.start);
        const after = input.value.slice(token.end);
        const next = `${before}${item.alias} ${after}`;
        const cursor = before.length + item.alias.length + 1;
        input.value = next;
        widget.value = next;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.focus();
        input.setSelectionRange?.(cursor, cursor);
        close();
    }

    function render() {
        menu.replaceChildren();
        if (!current.length) {
            const empty = document.createElement("div");
            empty.className = "h3-asset-autocomplete-empty";
            empty.textContent = "没有匹配的已连接素材";
            menu.appendChild(empty);
            return;
        }
        current.forEach((item, index) => {
            const row = document.createElement("div");
            row.className = `h3-asset-autocomplete-item${index === activeIndex ? " active" : ""}`;
            const title = document.createElement("div");
            title.className = "h3-asset-autocomplete-title";
            const alias = document.createElement("span");
            alias.className = "h3-asset-autocomplete-alias";
            alias.textContent = `${item.alias}  (${item.alternate})`;
            const native = document.createElement("span");
            native.className = "h3-asset-autocomplete-native";
            native.textContent = item.nativeLabel;
            const meta = document.createElement("div");
            meta.className = "h3-asset-autocomplete-meta";
            meta.textContent = `${item.kind} · ${item.source}`;
            title.append(alias, native);
            row.append(title, meta);
            row.addEventListener("mouseenter", () => {
                activeIndex = index;
                menu.querySelectorAll(".h3-asset-autocomplete-item").forEach((candidate, candidateIndex) => {
                    candidate.classList.toggle("active", candidateIndex === activeIndex);
                });
            });
            row.addEventListener("mousedown", (event) => {
                event.preventDefault();
                choose(item);
            });
            menu.appendChild(row);
        });
    }

    function refresh() {
        token = activeAtToken(input);
        if (!token) {
            close();
            return;
        }
        const query = token.query;
        current = collectAssetSuggestions(node).filter((item) => {
            const haystack = `${item.alias.slice(1)} ${item.alternate.slice(1)} ${item.kind}`.toLocaleLowerCase();
            return !query || haystack.includes(query);
        });
        activeIndex = Math.min(activeIndex, Math.max(0, current.length - 1));
        positionMenu();
        render();
        menu.hidden = false;
    }

    function onKeyDown(event) {
        if (menu.hidden) return;
        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            event.preventDefault();
            const direction = event.key === "ArrowDown" ? 1 : -1;
            activeIndex = (activeIndex + direction + Math.max(1, current.length)) % Math.max(1, current.length);
            render();
        } else if ((event.key === "Enter" || event.key === "Tab") && current[activeIndex]) {
            event.preventDefault();
            choose(current[activeIndex]);
        } else if (event.key === "Escape") {
            event.preventDefault();
            close();
        }
    }

    const onBlur = () => window.setTimeout(close, 150);
    input.addEventListener("input", refresh);
    input.addEventListener("click", refresh);
    input.addEventListener("keydown", onKeyDown);
    input.addEventListener("blur", onBlur);
    window.addEventListener("resize", close);
    window.addEventListener("scroll", close, true);

    return () => {
        input.removeEventListener("input", refresh);
        input.removeEventListener("click", refresh);
        input.removeEventListener("keydown", onKeyDown);
        input.removeEventListener("blur", onBlur);
        window.removeEventListener("resize", close);
        window.removeEventListener("scroll", close, true);
        menu.remove();
        delete input.dataset.h3AssetAutocomplete;
    };
}

function installWhenReady(node, attempt = 0) {
    const widget = node.widgets?.find((candidate) => candidate.name === "user_request");
    const input = widget?.inputEl ?? widget?.element?.querySelector?.("textarea, input");
    if (!widget || !input) {
        if (attempt < 20) window.setTimeout(() => installWhenReady(node, attempt + 1), 100);
        return;
    }
    node.__h3AssetAutocompleteCleanup?.();
    node.__h3AssetAutocompleteCleanup = attachAutocomplete(node, widget, input);
}

app.registerExtension({
    name: "MiniMaxH3.AssetAutocomplete",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_TYPE || nodeType.prototype[INSTALLED_FLAG]) return;
        nodeType.prototype[INSTALLED_FLAG] = true;

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalOnNodeCreated?.apply(this, arguments);
            window.setTimeout(() => installWhenReady(this), 0);
            return result;
        };

        const originalOnRemoved = nodeType.prototype.onRemoved;
        nodeType.prototype.onRemoved = function () {
            this.__h3AssetAutocompleteCleanup?.();
            this.__h3AssetAutocompleteCleanup = null;
            return originalOnRemoved?.apply(this, arguments);
        };
    },
});
