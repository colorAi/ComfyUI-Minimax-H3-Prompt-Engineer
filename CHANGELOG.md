# Changelog

All notable changes to MiniMax H3 Prompt Engineer are documented here.

## 0.4.4

- Persisted each AI provider's endpoint, model, site, and API key in a private local plugin configuration file.

## 0.4.3

- Made Basic, Medium, and Full scale both injected guide context and final prompt density; only Full loads the complete official writing guides.
- Added a pass-through Direct provider for ordinary prompts while retaining strict validation for preformatted H3 documents.
- Preserved each AI provider's model, endpoint, site, and API key while switching provider modes in the same node session.
- Excluded Registry-generated ZIP archives from source control and future publish archives.

## 0.4.2

- Fixed connected-asset autocomplete so `@` can immediately follow Chinese text without requiring whitespace.
- Preserved email and Latin-identifier boundaries to prevent unintended autocomplete menus.
- Updated the English and Simplified Chinese usage documentation for CJK `@asset` authoring.

## 0.4.1

- Rebuilt the English and Simplified Chinese README around the one-node workflow and smart `@asset` authoring.
- Added ComfyUI Registry metadata for the `hootoo` Publisher.
- Added deterministic node discovery metadata, Registry package exclusions, and a reviewed CLI publishing workflow.

## 0.4.0

- Added the unified `MiniMax H3 Prompt Studio + Generate` production node.
- Added RunningHub, OpenAI, local OpenAI-compatible, and Direct providers.
- Added Basic, Medium, and Full production prompt profiles.
- Added separate validated English execution and optional Simplified Chinese display outputs.
- Added connected-material autocomplete for `@imageN`, `@videoN`, `@video_audioN`, and `@audioN`.
- Added deterministic reference normalization, bounds checks, and soundtrack pairing validation.
- Added sampled-frame prompt analysis while preserving complete video batches for official H3 conditioning.

## 0.3.0

- Added direct integration with ComfyUI's official MiniMax H3 image-to-video and reference-to-video conditioning.
- Added single-connection image, video, and audio reference handling.
- Added selectable creative templates derived from MiniMax H3 production workflows.

## 0.2.2

- Adopted the GNU Affero General Public License v3.0 or later.
- Added SPDX identifiers across the Python and frontend source files.

## 0.2.1

- Added RunningHub prompt engineering, creative presets, site-specific model discovery, and multimodal image input.
- Added strict H3 prompt validation, timestamp checks, and automatic repair.
- Added English and Simplified Chinese documentation and example workflows.
