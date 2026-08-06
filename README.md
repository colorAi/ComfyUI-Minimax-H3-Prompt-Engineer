# ComfyUI MiniMax H3 Prompt Engineer

[English](README.md) | [简体中文](README_CN.md)

A production-oriented ComfyUI extension that converts short Chinese or English creative briefs into structured, validated English prompts for **MiniMax H3 video generation**. It supports RunningHub, OpenAI, local OpenAI-compatible models, selectable creative templates, and a unified node that reuses ComfyUI's official MiniMax H3 conditioning implementation so every reference asset is connected only once.

> Current version: `0.3.0`
> Node category: `MiniMax H3 / Prompt Engineer`

## Highlights

- Rewrites natural-language ideas into standardized MiniMax H3 prompt documents.
- Accepts Chinese or English input while preserving exact dialogue, lyrics, and visible text.
- Supports T2VA, I2VA, FL2VA, L2VA, and Full Reference task modes.
- Provides a unified Prompt Studio node that directly returns H3 conditioning and the joint AV latent.
- Shares one authoritative set of connected images, videos, video soundtracks, and standalone audio between prompt engineering and H3 conditioning.
- Resolves `@图像1`, `@视频1`, `@视频音频1`, and `@音频1` aliases with deterministic bounds and pairing validation.
- Supports RunningHub, OpenAI, local OpenAI-compatible servers, and a no-LLM Direct mode.
- Includes nine selectable creative directions distilled from the official MiniMax H3 skills.
- Converts simple shot descriptions into sequential `[Shot N]` blocks with valid cut timestamps.
- Accepts first-frame, last-frame, and multiple reference-image inputs.
- Provides structured presets for style, environment, lighting, framing, camera movement, sound, and music.
- Switches between RunningHub Global `.ai` and RunningHub China `.cn` endpoints.
- Refreshes the model catalog for the selected site and validates vision support when images are used.
- Performs deterministic structural validation and can automatically repair an invalid response once.
- Returns the finished prompt, validation report, raw model responses, and API usage metadata.

## RunningHub Registration Benefits

RunningHub remains available in the unified node and in the legacy prompt-only node. Choose the registration site that matches your region:

| Site | Registration benefit | Registration link |
| --- | --- | --- |
| RunningHub China | Register through the link and receive **1,000 RH Coins** | [Register on RunningHub China](https://www.runninghub.cn/?inviteCode=rh-v1123) |
| RunningHub Global | Register through the link and receive **1,000 RH Coins** | [Register on RunningHub Global](https://www.runninghub.ai/?inviteCode=rh-v1123) |

> These links include invite code `rh-v1123`. Eligibility, availability, credit delivery, and campaign terms are determined by RunningHub and may change over time.

## Included Nodes

### MiniMax H3 Prompt Studio + Generate (recommended)

This unified node combines prompt rewriting, validation, and ComfyUI's official `MiniMax H3 Image to Video` / `MiniMax H3 Reference to Video` conditioning paths.

It infers the H3 task from connected materials, expands friendly `@asset` aliases, generates and validates the prompt through the selected provider, and passes the final prompt plus the exact same normalized assets into the official H3 implementation. It returns `positive`, `latent`, the formatted prompt, validation report, raw LLM response, and usage metadata.

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

Choose a local vision model when reference images or sampled video frames need to be interpreted.

Provider API keys may be serialized into ComfyUI workflow JSON. Clear them before sharing a workflow, screenshot, or diagnostic package. The node does not intentionally include full keys in outputs or errors.

#### Safe `@asset` references

| User alias | H3 label | Connected material |
| --- | --- | --- |
| `@图像1` / `@image1` | `<Picture 1>` | First connected reference image |
| `@视频1` / `@video1` | `<Video 1>` | First connected reference video |
| `@视频音频1` / `@video_audio1` | `<Audio N>` | Soundtrack paired with reference video 1 |
| `@音频1` / `@audio1` | `<Audio N>` | First standalone reference audio |

The official H3 node numbers a reference video's soundtrack before standalone audio. Therefore `@音频1` is not always `<Audio 1>`. This extension computes the native label from the material's role, sorts Autogrow inputs numerically, reindexes gaps, and sends the same normalized dictionaries to both prompt construction and H3 conditioning. Missing aliases, out-of-range native labels, and orphan video soundtracks fail before an LLM request or H3 encoding begins.

Full Reference inputs cannot be mixed with `first_frame` / `last_frame`, because they use separate official H3 conditioning paths. Auto mode detects and reports that conflict.

#### Templates and multimodal behavior

The template dropdown includes General, 3D Animation Short, Brand Promo, Co-op Game Intro, Hand-drawn Live, Minimalist Product Ad, MV Subtitle, Paper Collage Explainer, and Papercraft Stop Motion. These are concise single-request directions distilled from the official MiniMax H3 skills in the local `MiniMax-H3/skills` repository; the bundled official writing guides remain authoritative for the output schema.

The prompt LLM receives reference images and at most three uniformly sampled frames from each reference video. The complete connected video batch is passed to the official MiniMax H3 node, which then applies its own target-length truncation and `17k+5` frame alignment before encoding. For broad Chat Completions compatibility, audio binary data is not sent to the prompt LLM; it receives labels, duration metadata, and the user's `reference_context`, while the complete audio is passed to MiniMax H3.

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
