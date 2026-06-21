# ShanHaiEdu LLM Provider 接口文档

**版本**：v1.0  
**日期**：2026-06-21  
**适用范围**：全链路冲刺轨道 B / C，覆盖教案生成与视频脚本链真实 LLM 调用。

---

## 1. 当前裁决

- 本轮全链路冲刺文本生成 provider 使用 DeepSeek。
- `PROVIDER_MODE=fake` 保留本地无密钥演示能力。
- `PROVIDER_MODE=real` 或 `PROVIDER_MODE=deepseek` 走 DeepSeek。
- `PROVIDER_MODE` 只控制文本 provider，不控制视频 provider。
- 视频 provider 由 `VIDEO_PROVIDER_MODE` 独立控制；默认 `placeholder`，不调用真实 Octo。
- 真实密钥只允许写入服务端环境变量或本地忽略文件，不得写入前端、源码、测试快照、提交信息或交接文档。

---

## 2. 环境变量

后端从以下位置读取配置：

```text
create_app(overrides) > 进程环境变量 > apps/api/.env / .env > 默认值
```

本地开发推荐写入 `apps/api/.env`：

```bash
PROVIDER_MODE=real
VIDEO_PROVIDER_MODE=placeholder
DEEPSEEK_API_KEY=<redacted>
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

说明：

| 变量 | 必填 | 说明 |
|---|---:|---|
| `PROVIDER_MODE` | 是 | `fake` / `real` / `deepseek` / `minimax`。本轮真实 LLM 使用 `real` 或 `deepseek`。 |
| `VIDEO_PROVIDER_MODE` | 否 | `placeholder` / `fake` / `real`。默认 `placeholder`；只有 `real` 才初始化真实 Octo 视频 provider。 |
| `DEEPSEEK_API_KEY` | real/deepseek 必填 | DeepSeek 服务端密钥。禁止提交。 |
| `DEEPSEEK_BASE_URL` | 否 | 默认 `https://api.deepseek.com`。 |
| `DEEPSEEK_MODEL` | 否 | 默认 `deepseek-chat`。 |

视频 provider 相关变量仅在 `VIDEO_PROVIDER_MODE=real` 时使用：

| 变量 | 必填 | 说明 |
|---|---:|---|
| `OCTO_API_KEY` | real 视频模式必填 | Octo 服务端密钥。禁止提交。 |
| `OCTO_BASE_URL` | 否 | 默认 `https://otuapi.com`。 |
| `OCTO_VIDEO_PROVIDER` | 否 | 默认 `octo`，保留 provider 标识。 |

TTS provider 相关变量仅在 `TTS_PROVIDER_MODE=real` 时使用：

| 变量 | 必填 | 说明 |
|---|---:|---|
| `TTS_PROVIDER_MODE` | 否 | `placeholder` / `real`。默认 `placeholder`；真实演示显式设为 `real`。 |
| `MINIMAX_API_KEY` | real TTS 必填 | Minimax TTS 服务端密钥。禁止提交。 |
| `MINIMAX_BASE_URL` | 否 | 默认 `https://api.minimaxi.com`。兼容旧变量 `MINMAX_BASE_URL`。 |
| `MINIMAX_TTS_MODEL` | 否 | 默认 `speech-2.8-hd`。兼容旧变量 `MINMAX_TTS_MODEL`。 |
| `MINIMAX_TTS_VOICE_ID` | 否 | 默认 `Chinese (Mandarin)_Gentleman`。 |

---

## 3. 后端调用模块

实现位置：

- `apps/api/app/providers.py`
  - `DeepSeekTextProvider`
  - `MinimaxTextProvider`
  - `MinimaxTTSProvider`
  - `FakeProvider`
- `apps/api/app/main.py`
  - 文本 provider 初始化和 `PROVIDER_MODE` 路由
  - 视频 provider 初始化和 `VIDEO_PROVIDER_MODE` 路由
  - TTS provider 初始化和 `TTS_PROVIDER_MODE` 路由
- `apps/api/app/services.py`
  - 节点 prompt 构建、LLM 调用、节点内容归一化
  - `final_video/generate` 的 TTS、SRT、concat manifest 和 final video 合成
- `apps/api/app/prompt_loader.py`
  - 文件 prompt 读取、`{{var}}` 渲染和 `{{include shared/xxx.md}}` 展开
- `apps/api/app/prompt_registry.py`
  - prompt DB seed、active/canary 版本读取、TTL 缓存和审计日志

统一调用接口：

```python
provider.complete_json(
    node_id=node_id,
    prompt=prompt,
    schema=schema,
    temperature=0.2,
    max_tokens=4000,
)
```

返回要求：

- 必须返回 JSON object。
- 可以兼容 fenced JSON，但 provider 会剥离代码块。
- 如果外层为 `{ "data": { ... } }`，provider 会自动解包 `data`。
- schema 的 `required` 字段缺失会抛 `ProviderError`。

常见错误码：

| 错误码 | 含义 | retryable |
|---|---|---:|
| `DEEPSEEK_KEY_MISSING` | 未配置 `DEEPSEEK_API_KEY` | false |
| `DEEPSEEK_BASE_URL_MISSING` | 未配置 base URL | false |
| `DEEPSEEK_REQUEST_FAILED` | HTTP 请求失败 | 视状态码而定 |
| `DEEPSEEK_RESPONSE_INVALID` | 返回结构不是 OpenAI-compatible chat completions | true |
| `DEEPSEEK_EMPTY_RESPONSE` | message content 为空 | true |
| `DEEPSEEK_JSON_INVALID` | 返回内容不是合法 JSON 或缺必填字段 | true |

Prompt 常见错误：

| 错误 | 含义 |
|---|---|
| `PromptTemplateMissing` | DB、文件或 include 找不到对应 prompt。 |
| `PromptVariableMissing` | prompt 中存在 `{{var}}`，但运行上下文未提供该变量。 |

TTS 常见错误码：

| 错误码 | 含义 | retryable |
|---|---|---:|
| `MINIMAX_TTS_KEY_MISSING` | 未配置 `MINIMAX_API_KEY` 或兼容旧变量。 | false |
| `MINIMAX_TTS_REQUEST_FAILED` | HTTP 请求失败。 | 视状态码而定 |
| `MINIMAX_TTS_RESPONSE_INVALID` | 返回结构没有可解析音频字段。 | true |
| `MINIMAX_TTS_AUDIO_INVALID` | 音频 hex/base64 解码失败。 | true |

---

## 4. 当前接入节点

### 4.1 `lesson_plan`

输入优先级：

1. `textbook_parse.selected_knowledge_point.markdown`
2. `textbook_parse` 当前内容

LLM 输出至少应包含：

```json
{
  "lesson_plan_markdown": "# 教案：5以内数的认识\n\n## 基本信息\n...",
  "intro_designs": []
}
```

服务层会补齐或归一化以下字段，保证兼容现有前端：

- `textbook_anchor`
- `teaching_objectives`
- `key_difficulty`
- `teaching_flow`
- `blackboard_design`
- `intro_designs`

### 4.2 视频脚本链 5 节点

已接入真实 LLM 入口：

1. `intro_selection`
2. `intro_video_script`
3. `intro_video_screenplay`
4. `intro_video_asset`
5. `storyboard`

其中 `storyboard` 兼容冲刺契约 3：

```json
{
  "total_duration": 90,
  "shots": [
    {
      "id": "S001",
      "duration": 10,
      "scene": "教室情境",
      "subject": "5个苹果摆在桌上",
      "subtitle": "今天我们来认识5以内的数",
      "visual_type": "animation"
    }
  ]
}
```

服务层会归一化为现有视频生成链需要的字段：

- `shot_id`
- `duration_sec`
- `main_subject`
- `reference_image_ids`
- `narration_slice`
- `subtitle`
- `model_prompt`
- `first_frame_test_status`
- `first_frame_asset_id`

---

## 5. Real E2E Acceptance Contract

真实端到端验收只接受同一轮证据目录中的可复核产物，不接受口头说明或 placeholder 冒充真实媒体。标准链路为：

```text
PDF → textbook_parse → lesson_plan → intro_selection → intro_video_script → intro_video_screenplay → intro_video_asset → storyboard → video clip → Minimax TTS → ffmpeg compose → outputs/final_video.mp4 → PPT
```

一轮真实验收必须满足：

- `summary.json` 中 `ok=true`。
- `generated-image-paths.json` 至少包含 1 个真实图片下载产物。
- `video-task-paths.json` 至少包含 1 个真实 `video_clip_generation` 成功任务。
- `final_video.mp4` 已下载，且 `ffprobe` 证明至少 1 条 audio stream。
- PPT 已导出并下载，压缩包内至少存在 1 个 `ppt/media/*.mp4`。
- `final_video` 节点内容必须包含：
  - `voice_gender=male`
  - `voice_language=zh-CN`
  - `audio_verified=true`
  - `english_audio_detected=false`
  - `narration_audio_path`
  - `subtitle_srt_path`
  - `concat_manifest_path`
  - `video_path=outputs/final_video.mp4`

执行命令示例：

```powershell
python scripts\t075_real_fullchain_smoke.py `
  --api-base http://127.0.0.1:8188 `
  --provider-mode real `
  --image-provider-mode real `
  --video-provider-mode real `
  --tts-provider-mode real `
  --min-successful-images 1 `
  --task-timeout-sec 1200 `
  --poll-interval-sec 15
```

安全边界：

- 文档、报告、测试快照、日志和交接记录只能写环境变量名，不得写真实密钥值。
- `--allow-placeholder-media` 只能用于结构冒烟，不能作为真实 E2E 通过依据。

---

## 6. 本地验证

无真实 key 的基础回归：

```powershell
python -m pytest apps\api\tests -q
```

DeepSeek provider 单元和 mock transport 回归：

```powershell
python -m pytest apps\api\tests\test_real_providers.py -q
```

Prompt/TTS/final video 专项回归：

```powershell
python -m pytest apps\api\tests\test_prompt_platform.py apps\api\tests\test_tts_and_final_video.py -q
```

Minimax TTS 本机 smoke：

```powershell
python -c "from pathlib import Path; from apps.api.app.settings import Settings; from apps.api.app.providers import MinimaxTTSProvider; s=Settings.from_overrides({'tts_provider_mode':'real'}); p=MinimaxTTSProvider(s.minmax_api_key, str(s.minmax_base_url) if s.minmax_base_url else None, s.minmax_tts_model, s.minmax_tts_voice_id); out=Path('storage')/'tts-smoke'/'narration.mp3'; p.synthesize('你好，山海教育测试。', out); print(out.as_posix(), out.stat().st_size)"
```

执行该 smoke 时只允许输出路径、大小、voice/model 等非敏感信息，不得输出 key。

真实 key smoke 建议只在本机执行，且不得打印密钥：

```powershell
cd E:\desktop\AI\02_Agents\lab\ShanHaiEdu
uvicorn apps.api.app.main:app --reload --port 8000
```

然后从前端或 API 触发：

```text
POST /projects/{project_id}/nodes/lesson_plan/generate
POST /projects/{project_id}/nodes/intro_selection/generate
```

本地完整演示建议显式保持：

```powershell
$env:PROVIDER_MODE="real"
$env:VIDEO_PROVIDER_MODE="placeholder"
```

这会让 DeepSeek 负责文本链路，同时 `final_video/generate` 走本地占位 MP4，不调用 Octo。

---

## 7. 安全要求

- `apps/api/.env` 必须保持 git ignore。
- `.env.example` 只能保留变量名和空占位。
- 测试中只能使用假 token 或 mock transport。
- 报错日志不得记录 Authorization header、API key、完整请求 payload 中的密钥。
- 前端不得读取 `DEEPSEEK_API_KEY`，所有真实 LLM 调用必须由后端发起。
- 前端不得读取 `OCTO_API_KEY`；真实视频 provider 只能由后端在 `VIDEO_PROVIDER_MODE=real` 时调用。
- 前端不得读取 `MINIMAX_API_KEY`；真实 TTS 只能由后端在 `TTS_PROVIDER_MODE=real` 时调用。
- `workflow/prompts/*.md` 是 Git 基线和灾难恢复源；运行时优先读取 Prompt DB active/canary 版本，文件只做 seed/fallback。
