# ComfyUI MiniMax H3 Prompt Engineer

[English](README.md) | [简体中文](README_CN.md)

一个面向 **MiniMax H3 视频生成**的 ComfyUI 提示词工程插件。它可以通过 RunningHub、OpenAI 或本地 OpenAI 兼容模型，把中文或英文创意整理为结构规范、可验证的英文视听提示词。新的一体化节点直接复用 ComfyUI 官方 MiniMax H3 conditioning 实现，同一份图片、视频和音频不需要再连接两遍。

> 当前版本：`0.3.0`
> 节点分类：`MiniMax H3 / Prompt Engineer`

插件内置并严格使用：

- `VIDEO_PROMPT_WRITING_GUIDE_base_en.md`
- `VIDEO_PROMPT_WRITING_GUIDE_ref_en.md`

## 功能亮点

- 把自然语言创意改写为标准化的 MiniMax H3 提示词文档。
- 支持中文或英文输入，并保留原始台词、歌词和画面文字。
- 支持五种 H3 任务模式和多镜头时间线。
- 提供一体化 `Prompt Studio + Generate` 节点，直接输出 `positive` conditioning 和 H3 视听 latent。
- 同一组图片、视频、视频配套音频和独立音频同时用于提示词理解与 H3 reference conditioning。
- 支持 `@图像1`、`@视频1`、`@视频音频1`、`@音频1` 素材引用，并在执行前校验越界和配对错误。
- 支持 RunningHub、OpenAI、本地 OpenAI 兼容服务和不调用 LLM 的 Direct 模式。
- 内置 9 个可选创作模板，来自官方 MiniMax H3 skills 的创作方向。
- 提供视觉风格、环境、灯光、镜头、运镜、声音和音乐预设。
- 支持 RunningHub 国内站 `.cn` 与国际站 `.ai` 切换。
- 根据所选站点动态刷新模型，并检查图片任务所需的视觉能力。
- 内置确定性格式校验和一次自动修复流程。

## RunningHub 注册福利

一体化节点和旧版独立提示词节点都可以继续使用 RunningHub 的 OpenAI 兼容 LLM API。可根据所在地区选择对应站点注册：

| 站点 | 注册福利 | 注册地址 |
| --- | --- | --- |
| RunningHub 国内站 | 点击注册赠送 **1000 RH 币** | [立即注册 RunningHub 国内站](https://www.runninghub.cn/?inviteCode=rh-v1123) |
| RunningHub 海外站 | 点击注册赠送 **1000 RH 币** | [立即注册 RunningHub 海外站](https://www.runninghub.ai/?inviteCode=rh-v1123) |

> 上述链接包含邀请码 `rh-v1123`。实际赠送规则、到账条件和活动有效期以 RunningHub 页面展示为准。

## 节点

安装后可在以下分类找到节点：

```text
MiniMax H3 / Prompt Engineer
```

### MiniMax H3 Prompt Studio + Generate（推荐）

这是新的一体化节点。它把提示词改写、结构校验以及 ComfyUI 官方的 `MiniMax H3 Image to Video` / `MiniMax H3 Reference to Video` conditioning 合并在一起。

主要流程：

1. 依据已连接素材自动判断 T2VA、I2VA、FL2VA、L2VA 或 Full Reference。
2. 把用户输入中的 `@素材` 映射成 H3 原生 `<Picture N>`、`<Video N>`、`<Audio N>`。
3. 用所选 AI 和模板生成、校验并按需修复提示词。
4. 将最终提示词和同一份素材直接交给 ComfyUI 官方 H3 节点实现。
5. 输出 `positive`、`latent`、最终提示词以及诊断信息；后续直接连接采样器。

AI 提供方：

| `ai_provider` | 用途 |
| --- | --- |
| `RunningHub` | 使用国内站或国际站 Chat Completions API |
| `OpenAI` | 使用 OpenAI Chat Completions；选择后可修改对应的 `model` |
| `Local OpenAI-compatible` | 支持提供 `/v1/chat/completions` 的 Ollama、LM Studio、vLLM 等服务 |
| `Direct · Prompt already formatted` | 不请求任何 LLM，把输入作为完整 H3 提示词直接校验和生成 conditioning |

本地服务示例：

```text
base_url: http://127.0.0.1:11434/v1
model: qwen3-vl:8b
api_key: 留空（除非本地服务要求）
```

本地模型必须自行支持所发送的 OpenAI Chat Completions 格式；使用图片或视频采样帧时，应选择视觉模型。

RunningHub、OpenAI 或本地服务的 API Key 都可能随 ComfyUI 工作流保存在 JSON 中。分享工作流、截图或诊断包前请清空 Key；节点的输出和错误信息不会主动包含完整 Key。

#### `@素材` 语法和编号安全

| 用户写法 | H3 原生标签 | 对应连接 |
| --- | --- | --- |
| `@图像1` / `@image1` | `<Picture 1>` | 第 1 个实际连接的 `ref_image` |
| `@视频1` / `@video1` | `<Video 1>` | 第 1 个实际连接的 `ref_video` |
| `@视频音频1` / `@video_audio1` | `<Audio N>` | 与第 1 个参考视频同编号的 soundtrack |
| `@音频1` / `@audio1` | `<Audio N>` | 第 1 个独立 `ref_audio` |

ComfyUI 官方 H3 节点规定音频标签按“各参考视频的配套音频在前，独立音频在后”编号。因此 `@音频1` 不一定是 `<Audio 1>`。本插件会按照素材语义自动换算真实编号，并把排序后的同一份字典交给官方节点，避免文字编号和实际 conditioning 顺序不一致。

如果写了不存在的 `@图像2`、把 `ref_video_audio_2` 接到了没有 `ref_video_2` 的位置，或显式写了越界的 `<Video 3>`，节点会在产生付费 LLM 请求或开始 H3 编码前报错。

Full Reference 素材和 `first_frame` / `last_frame` 属于 H3 的两条不同 conditioning 路径，不能混接。Auto 模式会明确拦截这种情况。

#### 可选创作模板

模板下拉框包含 General、3D 动画短片、品牌宣传片、合作游戏开场、手绘实拍融合、极简产品广告、MV 字幕、纸张拼贴解说和纸艺定格。它们是根据 MiniMax-H3 仓库 `skills/` 目录中的官方 skills 提炼出的单次提示词创作方向；H3 的正式字段规范仍以本仓库内两份官方 writing guide 为准。

#### 素材如何交给两个模型

- 提示词 AI 收到参考图片，以及每个参考视频最多 3 个均匀采样帧。
- 完整的参考视频帧批次会传给 ComfyUI 官方 H3 节点，再由官方实现按目标长度截断，并对齐到模型要求的 `17k+5` 帧数后编码。
- 为兼容不同 Chat Completions 服务，提示词 AI 不直接接收音频二进制，只收到音频编号、时长元数据和 `reference_context` 中的用户说明；实际音频仍完整交给 MiniMax H3。

### Minimax H3 Prompt Engineer · RunningHub

兼容旧工作流的独立提示词节点。它只调用 RunningHub，生成并验证最终提示词；素材仍需另外连接到 H3 conditioning 节点。新工作流建议使用上面的一体化节点。

主要输入：

| 输入 | 说明 |
| --- | --- |
| `runninghub_api_key` | RunningHub 企业级-共享 API Key |
| `runninghub_site` | 选择国内站 `.cn` 或国际站 `.ai` |
| `model` | 所选站点当前可用的模型列表 |
| `custom_model` | 可选的自定义模型 ID；填写后覆盖下拉框 |
| `task_mode` | MiniMax H3 任务模式 |
| `user_request` | 视频内容、镜头、切镜、台词、声音及参考需求 |
| `duration_seconds` | 目标视频的有效时长 |
| `reference_context` | 可选的参考素材角色、人物说明或上游音视频分析结果 |
| `auto_repair` | 首次结果不合格时自动修复一次 |
| `strict_validation` | 修复后仍不合格时停止工作流并报告错误 |

输出：

- `formatted_prompt`：可以直接连接 MiniMax H3 视频节点 `prompt` 输入的正式提示词。
- `validation_report`：结构检查结果。
- `raw_response`：初次响应及可能的修复响应。
- `usage_json`：模型、请求 ID 和 Token 用量。

### H3 Creative Presets

提供可选的视觉风格、环境、天气、灯光、景别、镜头角度、运镜、运镜幅度、速度、镜头结构、声音和音乐预设。

没有连接该节点时，所有创意参数由用户需求和参考图片决定。

## 安装

1. 下载并解压本仓库。
2. 将整个插件目录复制到：

```text
ComfyUI/custom_nodes/ComfyUI-Minimax-H3-Prompt-Engineer
```

3. 使用 ComfyUI 对应的 Python 环境安装依赖：

```bash
cd ComfyUI/custom_nodes/ComfyUI-Minimax-H3-Prompt-Engineer
python -m pip install -r requirements.txt
```

4. 完全重启 ComfyUI。
5. 在 `MiniMax H3 / Prompt Engineer` 分类中添加节点。

安装注意事项：

- 请复制完整目录，不要只复制 Python 文件。
- 一体化节点要求当前 ComfyUI 已包含官方 `comfy_extras/nodes_minimax_h3.py` 和 V3 节点 API；较旧版本只会加载原有提示词节点，请先更新 ComfyUI。
- `VIDEO_PROMPT_WRITING_GUIDE_base_en.md` 和 `VIDEO_PROMPT_WRITING_GUIDE_ref_en.md` 会在运行时读取，必须保留在插件根目录。
- 如果 ComfyUI 使用内置 Python 或虚拟环境，必须使用同一个解释器安装依赖。
- 更新插件后请刷新浏览器；站点选择没有出现时可清除前端缓存后重新加载。

## RunningHub 站点与 API Key

节点直接填写 `runninghub_api_key`。

`runninghub_site` 可以选择：

- `RunningHub Global (.ai)`：使用 `https://llm.runninghub.ai/v1/chat/completions`。
- `RunningHub China (.cn)`：使用 `https://llm.runninghub.cn/v1/chat/completions`。

插件会根据站点刷新 `model` 下拉框，并在后端再次检查模型是否属于所选站点。2026-08-03 实测 `.ai` 返回 59 个模型，`.cn` 返回 20 个模型；当时中国站的 20 个模型全部包含在国际站中，国际站另外提供 39 个 OpenAI、Anthropic、Google 和 xAI 模型。服务端清单可能随时调整，节点会优先读取各站实时 `/v1/models`。

默认的 `qwen/qwen3.6-plus` 两站均有，并且当前 `capabilities.vision=true`。前端无法刷新模型清单时会显示对应站点的内置备用模型；后端发现模型清单暂时不可访问时，则把最终可用性判断交给 RunningHub API。

RunningHub LLM API 只支持企业级-共享 API Key。请填写与所选站点对应、具有调用权限的 Key。

注意：节点值会随 ComfyUI 工作流保存，API Key 可能出现在工作流 JSON 中。分享工作流前务必清空 Key。插件不会在日志、错误报告或输出中显示完整 Key。

## 任务模式

| 模式 | 用途 | 旧版独立提示词节点输入 |
| --- | --- | --- |
| `T2VA · Text to Audiovisual` | 纯文字生成完整视听时间线 | 不接受图片 |
| `I2VA · First Frame to Audiovisual` | 从首帧向后发展 | 必须连接 `first_frame` |
| `FL2VA · First and Last Frames to Audiovisual` | 在首尾帧之间生成连续路径 | 必须连接 `first_frame` 和 `last_frame` |
| `L2VA · Last Frame to Audiovisual` | 从合理前态逐渐落到尾帧 | 必须连接 `last_frame` |
| `FULL_REFERENCE · Full Reference` | 人物、环境、图片、视频、音频等全参考关系 | `reference_images` 或 `reference_context` 至少一种 |

新的一体化节点还可以直接连接 `ref_images`、`ref_videos`、视频配套音频和独立 `ref_audios`；Auto 模式检测到这些输入后会自动选择 Full Reference。

连接任何图片输入时，需要选择 `capabilities.vision=true` 的 RunningHub 模型。默认模型是 `qwen/qwen3.6-plus`。

模型下拉框会尝试读取所选站点当前的 `/v1/models` 清单。如果启动时网络不可用，会显示内置备用模型。可将任意当前模型 ID 填入 `custom_model`，它会覆盖下拉框，但该模型仍必须存在于所选站点。

## 多镜头输入

用户可以使用自然中文简单列出镜头：

```text
8秒写实电影风格。
镜头1：雨夜街道，一个女人撑伞走向出租车，镜头缓慢跟随。
镜头2：3秒切到车内近景，她收起雨伞，看向窗外并说“我们走吧”。
镜头3：6秒切到车外，出租车驶离，固定镜头。
只有环境音，不要音乐。
```

插件会生成：

- `[Shot 1]`，不带时间戳。
- `[Shot 2] At 00:03.000, ...`
- `[Shot 3] At 00:06.000, ...`
- 中文台词保留为 `<d>[Chinese] 我们走吧</d>`。
- 独立的 `overall_soundscape` 和 `non_diegetic_music`。

基础模式生成结果中的 `integrated_multimodal_description:` 是内置 H3 写作规范要求的正式字段名，并非模型随机添加。

用户没有写切镜时间时，模型会在总时长内分配合理的递增时间。用户要求单一长镜头时只生成 `[Shot 1]`。

## 旧版独立提示词节点的图片与全参考

- `first_frame` 和 `last_frame` 都必须是单张 ComfyUI `IMAGE`。
- `reference_images` 可以使用 `IMAGE` 批次。
- 图片在发送前缩放到 `image_max_side`，再编码成 JPEG Base64。
- 旧版 RunningHub 提示词节点只直接接收图片；视频和音频需要先由上游节点分析，再把文字说明写进 `reference_context`。新的一体化节点可以直接连接视频和音频。

## 格式校验和修复

校验器检查：

- 字段名称和顺序。
- 模式对应的精确图片对齐指令。
- Shot 编号连续性。
- 首镜头无时间戳。
- 后续镜头使用 `MM:SS.mmm` 且严格递增。
- 切镜时间处于视频时长范围内。
- `<d>[Language] ...</d>` 格式。
- Full Reference 六段结构、任务前缀、引用标签和 retention marker。

`auto_repair=true` 时，首次响应不合格会自动调用同一模型修复一次。`strict_validation=true` 时，修复后仍不合格会停止工作流并显示具体错误。

## 建议参数

```text
temperature: 0.2
top_p: 0.9
max_tokens: 4096
reasoning_effort: none
timeout_seconds: 120
auto_repair: true
strict_validation: true
```

## 示例

- `examples/t2va_workflow.json`：ComfyUI 可视化工作流示例。
- `examples/t2va_api.json`：ComfyUI API 格式示例。

示例中的 API Key 为空，运行前必须在节点里填写自己的企业级-共享 Key。

## 测试

```bash
python -m unittest discover -s tests -v
```

## 说明

本项目是独立的 ComfyUI 扩展，并非 MiniMax 或 RunningHub 官方插件。模型能力、价格、注册奖励、API 权限及服务可用性以相关平台的最新说明为准。

## 开源协议

本项目遵循 [GNU Affero General Public License v3.0 或更高版本](LICENSE)。
