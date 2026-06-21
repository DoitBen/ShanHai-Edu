# T076 真实图片/视频/PPT 主链路专项回归

## 结论

【部分通过】：`intro_video_asset/generate` 不再返回 T069 旧错误 `400 / GENERATION_INPUT_INVALID / Expecting value`；本轮创建了 `image_generation` task，且 2 张真实图片成功落盘。但第 3 张图片生成在真实生图 provider submit 阶段返回 `502 / IMAGE_REQUEST_FAILED / Connection error.`，后端已写 `intro_video_asset=failed` 和 failed task。链路未推进到 storyboard、真实视频 clip、`final_video.mp4` 和 PPT，因此不足以支撑完整真实图片/视频/PPT 本地演示。

## 环境

- API：`http://127.0.0.1:8176`
- Web：`http://127.0.0.1:3176`
- Storage：`storage-t076-real-media-regression-20260621-181000`
- Provider：`PROVIDER_MODE=real`
- Image Provider：`IMAGE_PROVIDER_MODE=real`
- Video Provider：`VIDEO_PROVIDER_MODE=real`
- 项目 ID：`proj_b06c60b79093`
- 证据目录：`docs\qa-audits\t076-real-media-regression-evidence\20260621-184529`
- 密钥安全：未在报告、截图、控制台证据中输出真实密钥。

## API 证据

| 步骤 | 接口 | HTTP | 结果 |
| --- | --- | ---: | --- |
| 健康检查 | `GET /health` | 200 | `workflow_version=1.0.0` |
| 创建项目 | `POST /projects` | 200 | `proj_b06c60b79093` |
| 上传 PDF | `POST /projects/{id}/textbook` | 200 | fixture PDF 上传成功 |
| 教材解析 | `POST /projects/{id}/nodes/textbook_parse/generate` | 200 | `needs_review` |
| 确认教材解析 | `POST /projects/{id}/nodes/textbook_parse/approve` | 200 | `approved` |
| 教案生成 | `POST /projects/{id}/nodes/lesson_plan/generate` | 200 | `needs_review` |
| 确认教案 | `POST /projects/{id}/nodes/lesson_plan/approve` | 200 | `approved` |
| 导入策划 | `POST /projects/{id}/nodes/intro_selection/generate` | 200 | `needs_review` |
| 编辑 selected_anchor | `POST /projects/{id}/nodes/intro_selection/edit` | 200 | 保存成功 |
| 确认导入策划 | `POST /projects/{id}/nodes/intro_selection/approve` | 200 | `approved` |
| 视频脚本 | `POST /projects/{id}/nodes/intro_video_script/generate` | 200 | `needs_review` |
| 确认视频脚本 | `POST /projects/{id}/nodes/intro_video_script/approve` | 200 | `approved` |
| 分场剧本 | `POST /projects/{id}/nodes/intro_video_screenplay/generate` | 200 | `needs_review` |
| 确认分场剧本 | `POST /projects/{id}/nodes/intro_video_screenplay/approve` | 200 | `approved` |
| 视频资产/生图 | `POST /projects/{id}/nodes/intro_video_asset/generate` | 502 | `IMAGE_REQUEST_FAILED / Connection error.` |
| Manifest | `GET /projects/{id}/manifest` | 200 | `intro_video_asset=failed`，`storyboard=not_started` |
| Tasks | `GET /projects/{id}/tasks` | 200 | 3 个 `image_generation` task，2 completed，1 failed |

## 产物结果

- 历史阻塞点：通过回归。未再出现 `GENERATION_INPUT_INVALID / Expecting value`。
- 真实图片：
  - `asset_001.png` 已落盘，`1791450` bytes。
  - `asset_002.png` 已落盘，`1814474` bytes。
  - `asset_003.png` 失败，`IMAGE_REQUEST_FAILED`，`retryable=true`。
- Storyboard：未生成，`storyboard=not_started`。
- 真实视频 clip：未创建 `video_clip_generation` task，`video-task-paths.json=[]`。
- `final_video.mp4`：不存在。
- PPT：未导出，`.pptx` 不存在。

## 浏览器证据

- Web 真实 API 模式可登录并打开项目工作区。
- 首页项目卡片显示：`失败 / 当前阶段：视频资产 / 70%`。
- 工作区显示 10 个后端 manifest 节点，当前节点 `视频资产` 为失败状态；后续 `分镜脚本`、`最终视频` 节点入口可见但未推进。
- 浏览器控制台：`browser-console.json` 为空数组，无应用级 error/warn。
- 截图：`docs\qa-audits\t076-real-media-regression-evidence\20260621-184529\browser-workspace.png`

## 缺陷记录

### 严重 / Provider 外部失败阻断主链路

- 复现步骤：
  1. 使用 `PROVIDER_MODE=real`、`IMAGE_PROVIDER_MODE=real`、`VIDEO_PROVIDER_MODE=real` 启动隔离 API。
  2. 执行 `scripts\t075_real_fullchain_smoke.py` 指向 `http://127.0.0.1:8176`。
  3. 链路推进到 `intro_video_screenplay=approved` 后调用 `intro_video_asset/generate`。
- 实际结果：接口返回 `502 / IMAGE_REQUEST_FAILED / Connection error.`；`intro_video_asset` 写为 `failed`；第 3 个 `image_generation` task 为 failed；storyboard、视频、final_video、PPT 未生成。
- 期望结果：真实生图 provider 至少完成全部必需资产或支持可配置最小资产数量继续生成 storyboard；失败时可重试并能恢复链路。
- 影响范围：真实图片/视频/PPT 主链路无法完整演示；T076 通过标准未满足。
- 建议修复角色：后端工程师 + 运维/部署工程师联合排查真实生图 provider 网络连通性、账号池、超时/重试策略和最小成功图片数策略。

## 证据文件

- `summary.json`
- `manifest.json`
- `tasks.json`
- `tasks-sanitized.json`
- `node-intro_video_asset.json`
- `node-storyboard.json`
- `generated-image-paths.json`
- `video-task-paths.json`
- `clip-paths.json`
- `final-artifact-paths.json`
- `provider-error-summary.json`
- `browser-workspace.png`
- `browser-console.json`

## 后续建议

1. 后端/运维先处理 `IMAGE_REQUEST_FAILED / Connection error.` 的真实 provider 连接失败。
2. 若允许本地演示只需 1 张或 2 张参考图，应由首席系统架构师明确变更 T076 通过标准；当前标准要求继续到 storyboard、真实视频、final_video 和 PPT，本轮不能放行。
3. 修复后复用同一脚本重跑 T076，重点确认 `video_clip_generation` task、clip 下载、`outputs/final_video.mp4` 和 PPT 内视频引用。
