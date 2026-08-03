# ComfyUI MiniMax H3 Prompt Engineer

[English](README.md) | [简体中文](README_CN.md)

A production-oriented ComfyUI extension that converts short Chinese or English creative briefs into structured, validated English prompts for **MiniMax H3 video generation**. It uses the RunningHub OpenAI-compatible LLM API and supports multi-shot timelines, keyframe-guided generation, full-reference workflows, creative presets, and automatic format repair.

> Current version: `0.2.1`
> Node category: `MiniMax H3 / Prompt Engineer`

## Highlights

- Rewrites natural-language ideas into standardized MiniMax H3 prompt documents.
- Accepts Chinese or English input while preserving exact dialogue, lyrics, and visible text.
- Supports T2VA, I2VA, FL2VA, L2VA, and Full Reference task modes.
- Converts simple shot descriptions into sequential `[Shot N]` blocks with valid cut timestamps.
- Accepts first-frame, last-frame, and multiple reference-image inputs.
- Provides structured presets for style, environment, lighting, framing, camera movement, sound, and music.
- Switches between RunningHub Global `.ai` and RunningHub China `.cn` endpoints.
- Refreshes the model catalog for the selected site and validates vision support when images are used.
- Performs deterministic structural validation and can automatically repair an invalid response once.
- Returns the finished prompt, validation report, raw model responses, and API usage metadata.

## RunningHub Registration Benefits

This extension currently uses RunningHub's OpenAI-compatible LLM API. Choose the registration site that matches your region:

| Site | Registration benefit | Registration link |
| --- | --- | --- |
| RunningHub China | Register through the link and receive **1,000 RH Coins** | [Register on RunningHub China](https://www.runninghub.cn/?inviteCode=rh-v1123) |
| RunningHub Global | Register through the link and receive **1,000 RH Coins** | [Register on RunningHub Global](https://www.runninghub.ai/?inviteCode=rh-v1123) |

> These links include invite code `rh-v1123`. Eligibility, availability, credit delivery, and campaign terms are determined by RunningHub and may change over time.

## Included Nodes

### Minimax H3 Prompt Engineer · RunningHub

The main generation node builds the LLM request, calls RunningHub, cleans the response, validates its H3 structure, and optionally performs one automatic repair pass.

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

| Mode | Purpose | Required image input |
| --- | --- | --- |
| `T2VA · Text to Audiovisual` | Builds a complete audiovisual timeline from text | No images accepted |
| `I2VA · First Frame to Audiovisual` | Develops the video forward from a fixed first frame | `first_frame` |
| `FL2VA · First and Last Frames to Audiovisual` | Creates a continuous path between two keyframes | `first_frame` and `last_frame` |
| `L2VA · Last Frame to Audiovisual` | Builds a sequence that naturally converges on a final frame | `last_frame` |
| `FULL_REFERENCE · Full Reference` | Uses subject, image, video, and audio reference relationships | Images or `reference_context` |

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

The current release directly accepts images. Analyze video or audio with upstream ComfyUI nodes, then place the resulting asset labels, content, and intended roles in `reference_context`.

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


