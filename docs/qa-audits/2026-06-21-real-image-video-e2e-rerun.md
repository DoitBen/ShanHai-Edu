# T069 真实 API 全链路返工复测报告

日期：2026-06-21  
角色：测试工程师  
结论：【阻塞】  
验收口径：真实文本 provider + 真实生图 provider + 真实视频 provider，本地完整轻量 E2E，不做上线验收。

## 环境

- API：`http://127.0.0.1:8169`
- Web：`http://127.0.0.1:3169`
- Storage：`storage-t069-real-image-video-e2e-20260621-165407`
- Provider：`PROVIDER_MODE=real`
- 生图 Provider：`IMAGE_PROVIDER_MODE=real`
- 视频 Provider：`VIDEO_PROVIDER_MODE=real`
- Web：真实 API 模式，`NEXT_PUBLIC_DEMO_MODE=false`，`NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8169`
- 测试账号：`qa-t069`
- 项目 ID：`proj_0f50893204c6`
- 项目名：`T069 real image video e2e rerun 20260621-165442`
- 教材 fixture：`fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`
- 安全说明：未输出、截图或写入任何真实 DeepSeek / Octo / 生图 API 密钥。

## 证据文件

- 证据目录：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442`
- API summary：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\summary.json`
- Manifest：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\manifest-after-failure.json`
- Tasks：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\tasks-after-failure.json`
- 浏览器截图：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\browser-workspace.png`
- 浏览器控制台：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\browser-console.json`
- 浏览器可见状态：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\browser-visible-state.json`
- 真实图片路径清单：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\generated-image-paths.json`
- 视频 task/provider task 清单：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\task-id-lists.json`
- clip 路径清单：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\clip-paths.json`
- final video / PPT 路径清单：`docs\qa-audits\t069-real-image-video-evidence\20260621-165442\final-artifact-paths.json`

## 执行结果

| 验证项 | HTTP 状态 | 结果 | 证据 |
|---|---:|---|---|
| API `/health` | 200 | 通过 | `workflow_version=1.0.0` |
| Web 真实 API 模式启动 | 200 | 通过 | 登录页显示真实 API 模式 |
| 创建项目 | 200 | 通过 | `proj_0f50893204c6` |
| 上传教材 PDF | 200 | 通过 | `asset_e314a4eb1f2b` |
| 教材解析 `textbook_parse` | 200 | 通过 | 字段为 `math / 1 / renjiao / shang`，知识点 `kp_001` |
| 生成教案 `lesson_plan` | 200 | 通过 | `lesson_plan=approved` |
| 导入策划 `intro_selection` | 200 | 通过 | 生成、编辑 `selected_anchor`、确认均成功 |
| 视频脚本 `intro_video_script` | 200 | 通过 | `intro_video_script=approved` |
| 分场剧本 `intro_video_screenplay` | 200 | 通过 | `intro_video_screenplay=approved` |
| 图片资产 `intro_video_asset/generate` | 400 | 阻塞 | `GENERATION_INPUT_INVALID / Expecting value: line 1 column 1 (char 0)` |
| 创建 `image_generation` task | - | 未通过 | `tasks=[]` |
| 真实图片落盘 | - | 未通过 | `generated_image_paths=[]` |
| storyboard | 未执行 | 阻塞 | 上游图片资产未完成 |
| 真实视频 task / clip | 未执行 | 阻塞 | 无 video task id / provider task id |
| clip 下载 | 未执行 | 阻塞 | 无 clip 路径 |
| `final_video.mp4` | 未执行 | 阻塞 | `final_video_path=null` |
| PPT 导出与下载 | 未执行 | 阻塞 | `ppt_path=null` |
| 浏览器工作区 | 200 | 可展示阻塞状态 | 项目显示 `视频资产 / 70% / 进入「视频资产」`，节点 `视频资产 · 未开始` |
| 浏览器控制台 | - | 通过 | 应用级 `error/warn=[]` |

## 红线核验

- T069 明确要求 `intro_video_asset/generate` 不得再返回旧错误。
- 本轮有效复测仍返回：
  - HTTP：`400`
  - code：`GENERATION_INPUT_INVALID`
  - message：`Expecting value: line 1 column 1 (char 0)`
- 未观察到 T068 期望的新诊断错误码：
  - `INTRO_VIDEO_ASSET_JSON_EMPTY`
  - `INTRO_VIDEO_ASSET_JSON_INVALID`
  - `INTRO_VIDEO_ASSET_SCHEMA_INVALID`
- `intro_video_asset` 节点仍为 `not_started`，未写入 failed 节点版本。
- `tasks` 为空，未创建 `image_generation` task。

## 补充运行记录

第一次运行证据目录：`docs\qa-audits\t069-real-image-video-evidence\20260621-165138`。该轮在注入真实文本和视频配置后，生图 key 未被 API 进程读取，`intro_video_asset/generate` 返回 `502 / IMAGE_KEY_MISSING`。随后按项目私有生图配置文件将生图变量注入 API 进程并重启隔离服务，第二轮为本报告的有效复测结论。

## 阻塞缺陷

### 致命：T068 后 `intro_video_asset/generate` 仍复现旧黑盒错误，真实图片/视频/PPT 主链路无法继续

- 分类：后端 / Provider 错误处理 / 接口
- 复现步骤：
  1. 启动 API：`PROVIDER_MODE=real`、`IMAGE_PROVIDER_MODE=real`、`VIDEO_PROVIDER_MODE=real`，端口 `8169`，使用隔离 storage。
  2. 启动 Web：真实 API 模式，端口 `3169`。
  3. 创建项目并上传 fixture PDF。
  4. 依次生成并确认 `textbook_parse`、`lesson_plan`、`intro_selection`、`intro_video_script`、`intro_video_screenplay`。
  5. 调用 `POST /projects/proj_0f50893204c6/nodes/intro_video_asset/generate`。
- 实际结果：
  - 接口返回 `400 / GENERATION_INPUT_INVALID`。
  - message 为 `Expecting value: line 1 column 1 (char 0)`。
  - `intro_video_asset` 节点仍为 `not_started`，`current_version_id=null`。
  - `GET /projects/proj_0f50893204c6/tasks` 返回空数组。
  - 未创建 `image_generation` task，未产出真实图片、storyboard、真实视频 clip、`final_video.mp4` 和 PPT。
- 期望结果：
  - 如果 LLM 空响应，应返回 `502 / INTRO_VIDEO_ASSET_JSON_EMPTY` 并写入 failed 节点。
  - 如果 LLM 非 JSON，应返回 `502 / INTRO_VIDEO_ASSET_JSON_INVALID` 并写入 failed 节点。
  - 如果 LLM schema 缺字段，应返回 `502 / INTRO_VIDEO_ASSET_SCHEMA_INVALID` 并写入 failed 节点。
  - 如果 LLM 输出合法 assets JSON，应创建 `image_generation` task 并下载图片到项目目录。
- 影响范围：
  - PDF 到 PPT 主链路无法完成。
  - 真实图片、真实视频、final video、PPT 均无产物。
  - 前端只能展示项目停在 `视频资产 / 70%`，无法展示图片/视频任务状态或下载入口。
- 建议转交角色：后端工程师。
- 标准修复方案：
  - 回到 `intro_video_asset` 文本生成和图片 task 创建路径，确认所有 JSONDecodeError/空响应分支都被转换为 `ProviderError`，且不会漏到 `ValueError -> GENERATION_INPUT_INVALID`。
  - 为真实 provider 或等价 stub 补充集成级测试，覆盖从 `intro_video_screenplay=approved` 调用真实 `intro_video_asset/generate` 到创建 `image_generation` task 的完整路径。
  - 失败时必须写入 `intro_video_asset` failed 节点和 errors log，便于前端展示可诊断状态。

## 浏览器证据

- 首页真实 API 模式能读取项目卡片。
- 工作区能进入 `proj_0f50893204c6`。
- 可见状态：
  - 当前阶段：`视频资产`
  - 总进度：`70%`
  - 下一步动作：`进入「视频资产」`
  - 节点详情：`视频资产 · 未开始`
- 图片/视频任务状态不可见，原因是后端未创建 task。
- MP4/PPT 下载入口不可见，原因是上游阻塞导致无最终产物。
- 浏览器控制台：应用级 `error/warn` 为空。

## 最终结论

T069 结论：【阻塞】。

本轮已证明真实 API 链路仍可从 PDF 上传推进到 `intro_video_screenplay=approved`，但 T068 后 `intro_video_asset/generate` 仍复现旧红线错误 `400 / GENERATION_INPUT_INVALID / Expecting value`。未创建 `image_generation` task，未生成真实图片、真实视频 clip、`final_video.mp4` 或 PPT。建议转后端工程师继续返工，暂不能交给首席系统架构师做 T071 通过复核。
