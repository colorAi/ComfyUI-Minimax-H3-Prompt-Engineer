# ComfyUI MiniMax H3 Prompt Engineer

[English](README.md) | [简体中文](README_CN.md)

面向 **MiniMax H3 视频生成**的一体化 ComfyUI 提示词与 conditioning 节点。通过 RunningHub、OpenAI 或本地 OpenAI-compatible 模型构建可验证的 H3 视听提示词；图片、视频和音频只连接一次，并通过 `@素材` 贯穿 AI 理解、引用对齐与官方 H3 生成。

> 当前版本：`0.4.4`
> 节点分类：`MiniMax H3 / Prompt Engineer`

插件内置并严格使用：

- `VIDEO_PROMPT_WRITING_GUIDE_base_en.md`
- `VIDEO_PROMPT_WRITING_GUIDE_ref_en.md`

## 核心能力

- **单节点生成链**：提示词工程、结构校验、官方 H3 conditioning 和视听 latent 一次完成。
- **素材只连接一次**：图片、视频、视频配套音频和独立音频同时服务于 AI 理解与 H3 生成。
- **语义化素材寻址**：输入 `@` 即可选择已连接素材，自动插入 `@图像1`、`@视频1`、`@视频音频1` 或 `@音频1`。
- **专业提示词档位**：`Basic`、`Medium`、`Full` 三档控制模板上下文与制作规则密度。
- **多模型后端**：RunningHub、OpenAI、本地 OpenAI-compatible 服务及零 LLM 调用的 Direct 模式。
- **双语交付**：H3 使用经过校验的英文执行提示词，同时可输出简体中文阅读版本。
- **多模态引用**：支持 T2VA、I2VA、FL2VA、L2VA、Full Reference 和多镜头时间线。
- **确定性质量控制**：引用编号、配套音频、时间戳和 H3 文档结构在请求前后自动校验。

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

面向正式工作流的一体化节点。所有素材只连接到这里，节点自动完成素材编目、任务模式识别、提示词生成、结构校验和官方 H3 conditioning。

#### 单节点执行链

| 阶段 | 处理 |
| --- | --- |
| 素材编目 | 识别首尾帧、参考图像、参考视频、视频配套音频和独立音频 |
| 提示词工程 | 使用所选模板、请求深度和 AI provider 生成标准 H3 prompt |
| 引用对齐 | 将 `@素材` 转换为 H3 原生 `<Picture N>`、`<Video N>`、`<Audio N>` |
| 质量控制 | 校验任务结构、镜头时间、引用范围与音频配对；可自动修复一次 |
| H3 生成输入 | 调用 ComfyUI 官方 conditioning，实现同源素材、同序编号 |
| 节点输出 | `positive`、`latent`、`formatted_prompt`、`display_prompt` 及诊断数据 |

#### 快速使用

1. 连接 `clip`、`vae`，需要音频时连接 `audio_vae`。
2. 把图片、视频和音频连接到对应素材入口。
3. 选择 AI provider、创作模板、请求深度和输出语言。
4. 在 `user_request` 中输入 `@`，从菜单选择素材并完成创意描述。
5. 将 `positive` 与 `latent` 直接连接后续采样流程。

```text
以@图像1的人物为主角，让她进入@视频1的场景；
动作节奏跟随@视频音频1，结尾产品特写保持@图像2的材质与标识。
```

#### `@素材` 智能引用

`@` 菜单只展示当前已连接的素材，并同步显示素材类型、H3 原生标签和上游节点名称。中文文字后可直接连续输入 `@`，不要求添加空格；菜单同时支持关键词筛选、方向键导航以及 Enter/Tab 插入。

| 输入别名 | H3 原生标签 | 素材角色 |
| --- | --- | --- |
| `@图像1` / `@image1` | `<Picture 1>` | 参考图像或当前模式中的关键帧 |
| `@视频1` / `@video1` | `<Video 1>` | 参考视频 |
| `@视频音频1` / `@video_audio1` | `<Audio N>` | 与参考视频 1 配套的 soundtrack |
| `@音频1` / `@audio1` | `<Audio N>` | 独立参考音频 |

素材编号以实际连接为准。节点会压缩 Autogrow 空位、按数字顺序重排，并依据 H3 的“视频配套音频优先、独立音频随后”规则计算真实 `<Audio N>`。不存在的引用、越界编号和孤立的视频音频会在 LLM 请求与 H3 编码前终止。

#### 请求深度

| `request_level` | 注入内容 | Full Reference 正文目标 |
| --- | --- | --- |
| `Basic · 基础` | 精简 H3 必需格式与模板方向 | 约 180–260 个英文词 |
| `Medium · 中度` | 精简格式、模板专项、分镜、连续性、声音与质检 | 约 280–380 个英文词 |
| `Full · 完整` | 完整官方基础与 Full Reference Skills、全部制作规则 | 约 350–500 个英文词 |

三个等级同时控制请求上下文和输出详细度；只有 `Full` 注入完整官方写作指南。用户明确要求的镜头、台词、文字和引用关系不会因等级降低而省略。

#### 输出语言

| 选项 | `formatted_prompt` | `display_prompt` |
| --- | --- | --- |
| `English · H3 native` | H3 英文执行版本 | 同一英文版本 |
| `简体中文 · Display translation` | H3 英文执行版本 | 保留字段、时间戳和引用标签的中文阅读版本 |

使用 AI provider 时，中文显示会增加一次翻译调用。两种 Direct 模式不调用 AI，`formatted_prompt` 与 `display_prompt` 都保持用户输入语言。

AI 提供方：

| `ai_provider` | 用途 |
| --- | --- |
| `RunningHub` | 使用国内站或国际站 Chat Completions API |
| `OpenAI` | 使用 OpenAI Chat Completions；选择后可修改对应的 `model` |
| `Local OpenAI-compatible` | 支持提供 `/v1/chat/completions` 的 Ollama、LM Studio、vLLM 等服务 |
| `Direct · Use prompt as-is` | 不请求任何 LLM；转换 `@素材` 后把普通提示词原样交给 H3，不执行文档结构校验 |
| `Direct · Prompt already formatted` | 不请求任何 LLM；用于完整 H3 文档，并按当前任务模式执行严格结构校验 |

Direct 原样模式适合直接使用中文或英文普通提示词。`strict_validation` 不作用于该模式；素材越界、音频配对和 conditioning 输入仍照常检查。

各 AI provider 的站点、模型、服务地址和 API Key 会自动保存到插件目录的 `provider_config.json`，无需运行工作流。配置在 provider 切换、页面刷新和 ComfyUI 重启后仍会恢复；Direct 模式不写入配置。该文件已排除在 Git 和 Registry 发布包之外，并在系统支持时限制为仅文件所有者可读写。API Key 以本地明文保存，请保护插件目录，分享节点或工作流时不要复制此文件。

本地服务示例：

```text
base_url: http://127.0.0.1:11434/v1
model: qwen3-vl:8b
api_key: 留空（除非本地服务要求）
```

使用图片或视频采样帧时请选择视觉模型。API Key 可能写入 ComfyUI workflow JSON，分享工作流前请清空。

#### 可选创作模板

`General`、`3D 动画短片`、`品牌宣传片`、`合作游戏开场`、`手绘实拍融合`、`极简产品广告`、`MV 字幕`、`纸张拼贴解说`、`纸艺定格`。每个模板均提供从风格到制作规则的三档上下文。

#### 多模态素材通道

| 素材 | 提示词 AI | MiniMax H3 conditioning |
| --- | --- | --- |
| 图片 | 视觉理解与引用角色识别 | 原始 IMAGE tensor |
| 视频 | 每条视频最多 3 个均匀采样帧 | 完整帧批次，由官方实现截断并对齐到 `17k+5` |
| 音频 | 编号、时长与 `reference_context` 语义 | 完整音频数据 |

Full Reference 与 `first_frame` / `last_frame` 使用不同的官方 conditioning 路径，Auto 模式禁止混接。

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

### ComfyUI Manager / Registry

在 ComfyUI-Manager 中搜索 `MiniMax H3 Prompt Engineer` 并安装，或使用 Comfy CLI：

```bash
comfy node install minimax-h3-prompt-engineer
```

### 手动安装

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
