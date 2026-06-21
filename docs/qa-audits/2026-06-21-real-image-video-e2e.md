# T063 真实 API 全链路验收报告

日期：2026-06-21  
角色：测试工程师  
结论：阻塞  
验收口径：真实文本 LLM + 真实生图 provider + 真实视频 provider，本地完整轻量 E2E，不做上线验收。

## 环境

- API：`http://127.0.0.1:8163`
- Web：`http://127.0.0.1:3163`
- Storage：`storage-t063-real-image-video-e2e-20260621-155205`
- 文本 Provider：`PROVIDER_MODE=real`
- 生图 Provider：`IMAGE_PROVIDER_MODE=real`
- 视频 Provider：`VIDEO_PROVIDER_MODE=real`
- Web：真实 API 模式，`NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8163`
- 测试账号：`qa-t063`
- 项目 ID：`proj_6a0c9a3a6d81`
- 项目名：`T063真实全链路-20260621-160038`
- 教材 fixture：`fixtures\textbook-parsing\renjiao-grade1-volume1-2024\1上-人教版小学数学课本（2024新版）.pdf`
- 安全说明：未输出任何 DeepSeek / Octo / 生图 API 密钥。

## 证据文件

- API summary：`docs\qa-audits\t063-real-image-video-evidence\20260621-160039\summary.json`
- 浏览器截图：`docs\qa-audits\t063-real-image-video-evidence\20260621-160039\browser-workspace.png`
- 浏览器控制台：`docs\qa-audits\t063-real-image-video-evidence\20260621-160039\browser-console.json`
- 测试脚本：`scripts\t063_real_image_video_e2e.py`

## 执行结果

| 验证项 | HTTP 状态 | 结果 | 证据 |
|---|---:|---|---|
| API `/health` | 200 | 通过 | `status=ok`，`workflow_version=1.0.0` |
| Web 打开 | 200 | 通过 | 登录后首页可读取真实 API 项目 |
| 创建项目 | 200 | 通过 | 项目 ID `proj_6a0c9a3a6d81` |
| 上传教材 PDF | 200 | 通过 | `asset_62159a2ee685`，文件名已入库 |
| 教材解析 | 200 | 通过 | `textbook_parse=approved`，知识点 `kp_001` |
| 字段回填 / 知识点选择 | 200 | 通过 | `math / 1 / renjiao / shang`，`5以内数的认识` |
| 生成教案 | 200 | 通过 | `lesson_plan=approved`，包含 9 套导入方案输入 |
| 生成导入视频策划卡 | 200 | 通过 | `intro_selection/generate` 返回并选择 `design_story_01` |
| 编辑 `selected_anchor` | 200 | 通过 | 保存并 approve 成功 |
| 生成视频脚本 | 200 | 通过 | `intro_video_script=approved`，旁白落到 `selected_anchor` |
| 生成分场剧本 | 200 | 通过 | `intro_video_screenplay=approved` |
| 生成图片资产 | 400 | 阻塞 | `GENERATION_INPUT_INVALID`，消息 `Expecting value: line 1 column 1 (char 0)` |
| 真实生图产出参考图 | 未执行 | 阻塞 | `intro_video_asset/generate` 未创建 image task |
| 生成 storyboard | 未执行 | 阻塞 | 上游视频资产未完成 |
| 真实视频 API 产出 clip | 未执行 | 阻塞 | 上游 storyboard 未完成 |
| 下载 clip | 未执行 | 阻塞 | 无 video task |
| final_video.mp4 | 未执行 | 阻塞 | 无最终视频产物 |
| 导出 PPT | 未执行 | 阻塞 | 真实视频模式需 final_video.mp4 |
| PPT 内嵌视频 / 链接 | 未执行 | 阻塞 | 无 PPT |
| 浏览器控制台 | - | 通过 | 应用级 `error/warn=[]` |

## 阻塞缺陷

### 严重：真实链路在 `intro_video_asset/generate` 阻断，无法进入真实生图与真实视频

- 分类：后端 / Provider 错误处理 / 接口
- 复现步骤：
  1. 启动 API：`PROVIDER_MODE=real`、`IMAGE_PROVIDER_MODE=real`、`VIDEO_PROVIDER_MODE=real`，端口 `8163`。
  2. 启动 Web：真实 API 模式，端口 `3163`。
  3. 创建项目并上传 fixture PDF。
  4. 依次完成 `textbook_parse`、`lesson_plan`、`intro_selection`、`intro_video_script`、`intro_video_screenplay`。
  5. 调用 `POST /projects/proj_6a0c9a3a6d81/nodes/intro_video_asset/generate`。
- 实际结果：
  - 接口返回 `400`。
  - 响应体：`GENERATION_INPUT_INVALID`，`Expecting value: line 1 column 1 (char 0)`。
  - 同项目二次重试仍返回同样 `400`。
  - `tasks` 表为空，没有 `image_generation` task。
  - 未产出任何图片路径、视频 task id、clip、`final_video.mp4` 或 PPT。
- 期望结果：
  - `intro_video_asset/generate` 应返回 `200` 并生成资产 JSON。
  - 在 `IMAGE_PROVIDER_MODE=real` 下，应创建 `image_generation` task，下载参考图到 `assets/generated_images/{asset_id}.png`。
  - 若真实 LLM 输出非 JSON 或上游返回空响应，应返回可诊断 provider 错误，至少写入失败节点 / task / errors log，避免 400 黑盒中断。
- 风险影响：
  - T063 完整链路无法进入真实生图、storyboard、真实视频、final_video 和 PPT 导出。
  - 前端工作区只能停在“视频资产 / 70% / 未开始”，用户无法判断真实 provider 失败原因。
  - 真实 provider E2E 不具备可重复验收证据，后续视频链路验证被前置节点阻断。
- 建议转交角色：后端工程师。
- 标准修复方案：
  - 后端在真实 LLM `complete_json` 层补充空响应 / 非 JSON 的原始诊断脱敏记录，错误码建议区分为 `TEXT_PROVIDER_JSON_INVALID` 或节点级 `INTRO_VIDEO_ASSET_JSON_INVALID`。
  - `intro_video_asset/generate` 在文本生成成功后再创建 image task；如果文本生成失败，应写入节点失败版本或 errors log，前端可展示可读失败原因。
  - 为 `intro_video_asset` 增加 live-smoke 或 stub 回归：LLM 空响应、非 JSON、缺必填字段、真实图片 provider 成功、真实图片 provider 失败均需覆盖。

## 浏览器证据

- 首页真实 API 模式显示项目：
  - 当前阶段：`视频资产`
  - 总进度：`70%`
  - 下一步动作：`进入「视频资产」`
- 工作区显示：
  - 当前阶段：`视频资产`
  - 节点详情：`视频资产 · 未开始`
  - 可见按钮：`刷新状态`、`重新生成`、`生成草稿`
- 控制台：`browser-console.json` 中应用级 `error/warn` 为空。
- 备注：首次 Web 启动遇到 Turbopack `.next\dev` 缓存损坏 panic，清理 `apps\web\.next\dev` 后重启恢复；该问题属于本地 dev 缓存环境问题，未复现在浏览器应用控制台。

## 未覆盖项

由于 `intro_video_asset/generate` 阻塞，以下 T063 要求未能执行：

- 生成图片资产后的真实参考图路径。
- 视频任务 ID / provider task ID。
- 视频下载路径。
- `final_video.mp4` 路径。
- PPT 路径。
- PPT 内嵌视频或可下载视频链接有效性。

## 最终结论

T063 结论：【阻塞】。

本轮已证明真实 API 链路可以从 PDF 上传推进到分场剧本确认，但在视频资产节点调用真实链路时稳定返回 `400 / GENERATION_INPUT_INVALID`，阻断真实生图、真实视频、最终视频和 PPT 验收。需后端修复 `intro_video_asset/generate` 的真实 LLM 输出处理与失败诊断后，再安排测试工程师复测 T063。
