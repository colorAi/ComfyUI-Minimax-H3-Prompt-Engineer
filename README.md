# ComfyUI MiniMax H3 Prompt Engineer

[English](README.md) | [简体中文](README_CN.md)

An integrated ComfyUI prompt-orchestration and conditioning node for **MiniMax H3 video generation**. Build validated H3 audiovisual prompts with RunningHub, OpenAI, or a local OpenAI-compatible model; connect each image, video, and audio asset once, then address it through `@asset` across AI interpretation, reference alignment, and official H3 generation.

> Current version: `0.4.2`
> Node category: `MiniMax H3 / Prompt Engineer`

## Core capabilities

- **One-node generation path**: prompt engineering, schema validation, official H3 conditioning, and joint AV latent generation.
- **Connect every asset once**: images, videos, paired soundtracks, and standalone audio feed both AI interpretation and H3 generation.
- **Semantic asset addressing**: type `@` to select a connected asset and insert `@image1`, `@video1`, `@video_audio1`, or `@audio1`.
- **Production prompt profiles**: Basic, Medium, and Full levels control template context and production-rule density.
- **Multiple AI backends**: RunningHub, OpenAI, local OpenAI-compatible servers, and zero-LLM Direct mode.
- **Bilingual delivery**: H3 receives a validated English execution prompt; an optional Simplified Chinese display prompt is returned separately.
- **Full H3 mode coverage**: T2VA, I2VA, FL2VA, L2VA, Full Reference, and multi-shot timelines.
- **Deterministic quality control**: validates asset bounds, soundtrack pairing, timestamps, and H3 document structure.

## RunningHub Registration Benefits

RunningHub remains available in the unified node and in the legacy prompt-only node. Choose the registration site that matches your region:

| Site | Registration benefit | Registration link |
| --- | --- | --- |
| RunningHub China | Register through the link and receive **1,000 RH Coins** | [Register on RunningHub China](https://www.runninghub.cn/?inviteCode=rh-v1123) |
| RunningHub Global | Register through the link and receive **1,000 RH Coins** | [Register on RunningHub Global](https://www.runninghub.ai/?inviteCode=rh-v1123) |

> These links include invite code `rh-v1123`. Eligibility, availability, credit delivery, and campaign terms are determined by RunningHub and may change over time.

## Included Nodes

### MiniMax H3 Prompt Studio + Generate (recommended)

The production node for new workflows. Connect all assets here once; the node handles asset indexing, task-mode inference, prompt generation, validation, and official H3 conditioning.

#### One-node execution path

| Stage | Operation |
| --- | --- |
| Asset indexing | Detects keyframes, reference images, videos, paired soundtracks, and standalone audio |
| Prompt engineering | Applies the selected template, request depth, and AI provider |
| Reference alignment | Resolves `@asset` aliases into native `<Picture N>`, `<Video N>`, and `<Audio N>` labels |
| Quality control | Validates task schema, shot timing, reference bounds, and soundtrack pairing; repairs once when enabled |
| H3 conditioning | Calls ComfyUI's official implementation with the same normalized assets and ordering |
| Outputs | Returns `positive`, `latent`, `formatted_prompt`, `display_prompt`, and diagnostics |

#### Quick start

1. Connect `clip` and `vae`; connect `audio_vae` when the workflow uses audio.
2. Connect images, videos, and audio to the matching material inputs.
3. Select the AI provider, creative template, request depth, and display language.
4. Type `@` in `user_request`, select materials, and finish the creative brief.
5. Connect `positive` and `latent` to the downstream sampling workflow.

```text
Use the character from @image1 as the lead and move her into the setting of @video1.
Match the action rhythm to @video_audio1; preserve the material and logo from @image2 in the final product close-up.
```

#### Smart `@asset` references

The `@` menu lists only connected assets and displays each alias, native H3 label, asset role, and upstream node. In CJK text, `@` can immediately follow the preceding character without whitespace. The menu supports filtering, arrow-key navigation, and Enter/Tab insertion.

| Alias | Native H3 label | Asset role |
| --- | --- | --- |
| `@image1` | `<Picture 1>` | Reference image or mode-specific keyframe |
| `@video1` | `<Video 1>` | Reference video |
| `@video_audio1` | `<Audio N>` | Soundtrack paired with reference video 1 |
| `@audio1` | `<Audio N>` | Standalone reference audio |

Numbering follows actual connections. The node compacts Autogrow gaps, applies numeric ordering, and calculates native audio labels with paired video soundtracks before standalone audio. Missing references, out-of-range labels, and orphan soundtracks fail before any LLM request or H3 encoding.

#### Request depth

| `request_level` | Best for | Injected production context |
| --- | --- | --- |
| `Basic · 基础` | Clear briefs and fast rewrites | Core template direction and H3 schema |
| `Medium · 中度` | Balanced production work | Template rules, shot design, continuity, audio, and quality control |
| `Full · 完整` | Ads, music videos, and narrative work requiring maximum control | Beats, visual system, motion, camera, text, reference retention, and final checks |

#### Display language

| Option | `formatted_prompt` | `display_prompt` |
| --- | --- | --- |
| `English · H3 native` | English H3 execution prompt | Same English prompt |
| `简体中文 · Display translation` | English H3 execution prompt | Chinese reading version with schema, timestamps, and reference tags preserved |

Chinese display output adds one translation call. Direct mode returns the English execution prompt only.

Available providers:

| Provider | Behavior |
| --- | --- |
| `RunningHub` | Uses the selected Global or China Chat Completions endpoint |
| `OpenAI` | Uses OpenAI Chat Completions and the selected provider's `model` field |
| `Local OpenAI-compatible` | Uses an Ollama, LM Studio, vLLM, or similar `/v1/chat/completions` server |
| `Direct · Prompt already formatted` | Makes no LLM request; validates and conditions an already-formatted H3 prompt |

Typical local configuration:

```text
base_url: http://127.0.0.1:11434/v1
model: qwen3-vl:8b
api_key: empty unless your server requires it
```

Use a local vision model when images or sampled video frames must be interpreted. Provider keys may be serialized into ComfyUI workflow JSON; clear them before sharing a workflow.

#### Templates and multimodal behavior

Templates: General, 3D Animation Short, Brand Promo, Co-op Game Intro, Hand-drawn Live, Minimalist Product Ad, MV Subtitle, Paper Collage Explainer, and Papercraft Stop Motion. Every template supports Basic, Medium, and Full production context.

| Asset | Prompt AI | MiniMax H3 conditioning |
| --- | --- | --- |
| Image | Visual interpretation and reference-role analysis | Original IMAGE tensor |
| Video | Up to three uniformly sampled frames per video | Full frame batch, truncated and aligned to `17k+5` by the official implementation |
| Audio | Reference label, duration, and `reference_context` semantics | Complete audio data |

Full Reference and `first_frame` / `last_frame` use separate official conditioning paths; Auto mode rejects mixed connections.

### Minimax H3 Prompt Engineer · RunningHub

This legacy-compatible prompt-only node builds the LLM request, calls RunningHub, cleans the response, validates its H3 structure, and optionally performs one automatic repair pass. New workflows should prefer the unified node so assets do not need duplicate connections.

Key inputs:

| Input | Description |
| --- | --- |
| `runninghub_api_key` | RunningHub Enterprise-Shared API Key |
| `runninghub_site` | Selects the Global `.ai` or China `.cn` API |
| `model` | Model catalog for the selected site |
| `custom_model` | Optional model ID that overrides the dropdown selection |
| `task_mode` | MiniMax H3 generation mode |
| `user_request` | Video content, shots, cuts, dialogue, sound, and reference requirements |
| `duration_seconds` | Effective target-video duration |
| `reference_context` | Optional reference roles, speaker notes, or upstream video/audio analysis |
| `temperature`, `top_p` | LLM sampling controls |
| `max_tokens` | Maximum completion length |
| `reasoning_effort` | Reasoning level when supported by the selected model |
| `auto_repair` | Repairs an invalid first response once |
| `strict_validation` | Stops the workflow if the repaired result is still invalid |

Optional connections:

- `creative_presets`: output from the H3 Creative Presets node.
- `first_frame`: one ComfyUI `IMAGE` used as the first-frame anchor.
- `last_frame`: one ComfyUI `IMAGE` used as the final-frame anchor.
- `reference_images`: one image or an image batch for Full Reference mode.

Outputs:

| Output | Description |
| --- | --- |
| `formatted_prompt` | Cleaned and validated MiniMax H3 prompt document |
| `validation_report` | Deterministic format-validation result |
| `raw_response` | Initial LLM response and optional repair response |
| `usage_json` | Selected site, endpoint, model, request IDs, and token usage |

### H3 Creative Presets

An optional structured-control node covering:

- visual style and environment;
- time, weather, and lighting;
- shot size and camera angle;
- camera motion, amplitude, and speed;
- single-shot or multi-shot structure;
- soundscape and non-diegetic music;
- additional custom production constraints.

Values left on `Auto` are inferred from the user's request and reference material.

## Supported Task Modes

| Mode | Purpose | Legacy prompt-only node input |
| --- | --- | --- |
| `T2VA · Text to Audiovisual` | Builds a complete audiovisual timeline from text | No images accepted |
| `I2VA · First Frame to Audiovisual` | Develops the video forward from a fixed first frame | `first_frame` |
| `FL2VA · First and Last Frames to Audiovisual` | Creates a continuous path between two keyframes | `first_frame` and `last_frame` |
| `L2VA · Last Frame to Audiovisual` | Builds a sequence that naturally converges on a final frame | `last_frame` |
| `FULL_REFERENCE · Full Reference` | Uses subject, image, video, and audio reference relationships | `reference_images` or `reference_context` |

The unified node additionally accepts `ref_images`, `ref_videos`, paired video soundtracks, and standalone `ref_audios` directly. Its Auto mode selects Full Reference whenever any of those inputs are connected.

Image-based modes require a RunningHub model whose `/v1/models` metadata reports `capabilities.vision=true`. The default `qwen/qwen3.6-plus` model was available on both sites and reported vision support at the time of verification.

## Installation

### ComfyUI Manager / Registry

Search for `MiniMax H3 Prompt Engineer` in ComfyUI-Manager, or install the Registry package with Comfy CLI:

```bash
comfy node install minimax-h3-prompt-engineer
```

### Manual installation

1. Download and extract this repository.
2. Copy the complete directory to:

```text
ComfyUI/custom_nodes/ComfyUI-Minimax-H3-Prompt-Engineer
```

3. Install the dependency in the Python environment used by ComfyUI:

```bash
cd ComfyUI/custom_nodes/ComfyUI-Minimax-H3-Prompt-Engineer
python -m pip install -r requirements.txt
```

4. Restart ComfyUI completely.
5. Add the nodes from `MiniMax H3 / Prompt Engineer`.

### Important installation notes

- Copy the entire repository, not only the Python files.
- The unified node requires a current ComfyUI build containing the official `comfy_extras/nodes_minimax_h3.py` module and the V3 node API. Older builds load only the legacy prompt nodes; update ComfyUI first.
- `VIDEO_PROMPT_WRITING_GUIDE_base_en.md` and `VIDEO_PROMPT_WRITING_GUIDE_ref_en.md` are loaded at runtime and must remain in the plugin root.
- If ComfyUI uses a bundled Python runtime or virtual environment, install dependencies with that exact interpreter.
- After updating the extension, refresh the browser page. Clear the frontend cache if the site selector does not appear.

## RunningHub API Setup

1. Obtain a RunningHub Enterprise-Shared API Key with LLM access.
2. Select the matching site in `runninghub_site`.
3. Paste the key into `runninghub_api_key`.
4. Select a model from the site-specific `model` dropdown.

| Site | Chat Completions endpoint |
| --- | --- |
| RunningHub Global `.ai` | `https://llm.runninghub.ai/v1/chat/completions` |
| RunningHub China `.cn` | `https://llm.runninghub.cn/v1/chat/completions` |

The Global and China sites can expose different model catalogs. The extension reads the selected site's live `/v1/models` endpoint, provides a site-specific fallback list during discovery outages, and checks the site/model combination before making a paid completion request.

> **API key security:** ComfyUI may serialize widget values into workflow JSON. Always clear `runninghub_api_key` before sharing a workflow, screenshot, or diagnostic package. The extension does not intentionally include the full key in its outputs or errors.

## Basic Usage

Enter a concise Chinese or English production brief in `user_request`. For example:

```text
8 seconds, cinematic live action.
Shot 1: On a rainy street at night, a woman holding an umbrella walks toward a taxi; the camera follows slowly.
Shot 2: Cut at 3 seconds to a close-up inside the car. She closes the umbrella, looks through the window, and says “我们走吧”.
Shot 3: Cut at 6 seconds to an exterior view. The taxi drives away in a static shot.
Use environmental sound only, with no music.
```

The extension turns this into a formal prompt with:

- sequential `[Shot 1]`, `[Shot 2]`, and `[Shot 3]` blocks;
- strictly increasing `MM:SS.mmm` cut timestamps for later shots;
- the original dialogue preserved as `<d>[Chinese] 我们走吧</d>`;
- separate soundscape and non-diegetic music fields.

Base-mode prompts contain the `integrated_multimodal_description:` field. This is a required field in the bundled H3 writing specification, not a random model prefix.

## Validation and Automatic Repair

The deterministic validator checks:

- required field names and ordering;
- mode-specific image-alignment instructions;
- sequential shot numbering;
- absence of a timestamp on Shot 1;
- timestamp syntax, ordering, and duration bounds on later shots;
- `<d>[Language] ...</d>` dialogue syntax;
- Full Reference sections, task prefixes, reference labels, and retention markers.

Recommended settings:

```text
auto_repair: true
strict_validation: true
```

If the first response is invalid, the extension asks the same model to repair it once with deterministic sampling settings. Strict mode stops the workflow if the repaired response still fails validation.

## Recommended Parameters

```text
temperature: 0.2
top_p: 0.9
max_tokens: 4096
reasoning_effort: none
timeout_seconds: 120
image_max_side: 1536
auto_repair: true
strict_validation: true
```

Support for `reasoning_effort`, context length, and multimodal input varies by model. Use the current RunningHub model metadata as the source of truth.

## Example Workflows

- `examples/t2va_workflow.json`: ComfyUI visual-workflow example.
- `examples/t2va_api.json`: ComfyUI API-format example.

The examples intentionally contain an empty API key. Enter your own key before execution and clear it again before sharing the workflow.

## Troubleshooting

### The complete model catalog is not visible

Verify `runninghub_site` and confirm that both the ComfyUI server and browser can reach the site's `/v1/models` endpoint. During a discovery failure, the node shows a smaller fallback list. An exact model ID can also be entered in `custom_model`, but it must still exist on the selected site.

### The selected model does not support vision

The model reports `capabilities.vision=false`. Select a vision-capable model for image-based modes, or use T2VA for a text-only workflow.

### The response fails strict validation

Enable `auto_repair`, keep `strict_validation` enabled, increase `max_tokens` if the response was truncated, and select a model with stronger instruction-following performance.

### How are video and audio references used?

The unified node passes the connected video batch and audio to ComfyUI's official H3 reference-conditioning implementation. The prompt LLM receives at most three uniformly sampled video frames plus audio labels, duration metadata, and the user's `reference_context`. The legacy RunningHub prompt-only node still requires upstream video/audio analysis in `reference_context`.

## Development and Tests

Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

The tests cover API response parsing, site-isolated model caching, task modes, multimodal message construction, response cleaning, structural validation, and automatic repair.

## Disclaimer

This is an independent ComfyUI extension and is not an official MiniMax or RunningHub product. Model availability, pricing, registration rewards, API permissions, and service behavior are governed by the respective platforms and may change without notice.

<img width="2324" height="1594" alt="ScreenShot_2026-08-03_155337_450" src="https://github.com/user-attachments/assets/377fde29-cfd1-420f-99d6-5836f7fd9cea" />



https://github.com/user-attachments/assets/20d196d2-1eab-41c3-8f69-76116d52e6ca

## License

This project is licensed under the [GNU Affero General Public License v3.0 or later](LICENSE).
